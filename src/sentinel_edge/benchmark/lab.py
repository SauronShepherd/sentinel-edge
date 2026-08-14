from __future__ import annotations

import hashlib
import json
import math
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field

from sentinel_edge.domain.models import BenchmarkVariant, ClaimClass, CriticalityTier, HazardKind, OpportunityDisposition, ResourceSnapshot, RuntimeMode, WorkloadSpec
from sentinel_edge.runtime import VirtualClock, WorkloadScheduler


class BenchmarkOpportunity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    opportunity_key: str
    workload_id: str
    hazard: HazardKind
    tier: CriticalityTier
    scheduled_offset_ms: int = Field(ge=0)
    captured_offset_ms: int = Field(ge=0)
    deadline_ms: int = Field(gt=0)
    max_deferral_ms: int = Field(ge=0)
    memory_mb: int = Field(gt=0)
    profile_id: str
    service_ms: dict[BenchmarkVariant, int]


class BenchmarkRun(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    variant: BenchmarkVariant
    claim_class: ClaimClass
    schedule_digest: str
    offered: int
    processed: int
    skipped: int
    deadline_misses: int
    median_end_to_end_ms: float
    p50_end_to_end_ms: float
    p95_end_to_end_ms: float
    p99_end_to_end_ms: float
    latency_histogram: dict[str, Any]
    raw_latency_samples_ms: tuple[float, ...]
    latency_overflow_count: int = Field(ge=0)
    resource_samples: tuple[dict[str, Any], ...]
    total_service_ms: int = Field(ge=0)
    total_queue_delay_ms: int = Field(ge=0)
    heavy_model_invocation_count: int = Field(ge=0)
    heavy_model_service_ms: int = Field(ge=0)
    heavy_model_duty_cycle: float = Field(ge=0.0, le=1.0)
    scheduler_decision_count: int = Field(ge=0)
    hazard_quality: dict[str, dict[str, int | float]]
    opportunity_accounting: dict[str, int]
    execution_mode: str
    instrumentation_config_hashes: tuple[str, ...]
    telemetry_policy_digest: str
    quality_scope: str
    camera_preprocessing: dict[str, Any]
    records: tuple[dict[str, Any], ...]


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(0, min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1))
    return ordered[rank]


class DeterministicBenchmarkLab:
    """Open-loop deterministic replay. Results are explicitly simulated, never target measurements."""

    def run(self, manifest: dict[str, Any], variant: BenchmarkVariant) -> BenchmarkRun:
        policy = manifest.get("benchmark_policy")
        if not isinstance(policy, dict) or policy.get("arrival_mode") != "open_loop":
            raise ValueError("benchmark_policy must predeclare open_loop arrival_mode")
        if policy.get("primary_tail_metric") != "p99_end_to_end_ms" or not policy.get("miss_policy"):
            raise ValueError("benchmark_policy must declare primary tail metric and miss policy")
        if int(policy.get("warmup_runs", 0)) < 1 or int(policy.get("repeats", 0)) < 2 or policy.get("steady_state") is not True:
            raise ValueError("benchmark_policy must declare warmup, repeats, and steady_state")
        if variant is BenchmarkVariant.O1 and policy.get("online_quality_scope") != "timed_run_only":
            raise ValueError("O1 benchmark must declare timed_run_only quality scope")
        instrumentation = manifest.get("release_instrumentation")
        if not isinstance(instrumentation, dict):
            raise ValueError("release_instrumentation must declare config_hashes and telemetry_policy")
        config_hashes = tuple(sorted(str(value) for value in instrumentation.get("config_hashes", ())))
        telemetry_policy = instrumentation.get("telemetry_policy")
        if not config_hashes or not isinstance(telemetry_policy, dict):
            raise ValueError("release_instrumentation must declare config_hashes and telemetry_policy")
        camera_preprocessing = instrumentation.get("camera_preprocessing")
        if not isinstance(camera_preprocessing, dict) or not {"opencv_enabled", "kleidicv_enabled", "backend_version", "build", "thread_policy", "operations"} <= camera_preprocessing.keys():
            raise ValueError("release_instrumentation must declare camera preprocessing identity")
        telemetry_policy_digest = hashlib.sha256(
            json.dumps(telemetry_policy, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        start = datetime.fromisoformat(manifest["start_at"].replace("Z", "+00:00"))
        opportunities = [BenchmarkOpportunity.model_validate(item) for item in manifest["opportunities"]]
        schedule_payload = [
            {
                "opportunity_key": item.opportunity_key,
                "workload_id": item.workload_id,
                "hazard": item.hazard.value,
                "scheduled_offset_ms": item.scheduled_offset_ms,
                "captured_offset_ms": item.captured_offset_ms,
            }
            for item in opportunities
        ]
        schedule_digest = hashlib.sha256(
            json.dumps(schedule_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        if variant is BenchmarkVariant.O1:
            records, scheduler_decision_count = self._run_orchestrated(
                start, opportunities, variant, manifest.get("resources", {})
            )
        else:
            records = self._run_fixed(start, opportunities, variant)
            scheduler_decision_count = 0
        end_to_end = [float(item["end_to_end_ms"]) for item in records if item["disposition"] == "processed"]
        processed_records = [item for item in records if item["disposition"] == "processed"]
        total_service_ms = sum(int(item.get("service_ms") or 0) for item in processed_records)
        total_queue_delay_ms = sum(int(item.get("queue_latency_ms") or 0) for item in processed_records)
        heavy_workload_ids = {str(value) for value in manifest.get("heavy_workload_ids", ["wildfire-stage2"])}
        heavy_records = [item for item in processed_records if item["workload_id"] in heavy_workload_ids]
        heavy_model_service_ms = sum(int(item.get("service_ms") or 0) for item in heavy_records)
        completion_values = [int(item["completion_ms"]) for item in processed_records if item.get("completion_ms") is not None]
        capture_values = [int(item["capture_ms"]) for item in records]
        horizon_ms = max(1, (max(completion_values) if completion_values else 1) - (min(capture_values) if capture_values else 0))
        heavy_model_duty_cycle = min(1.0, heavy_model_service_ms / horizon_ms)
        misses = sum(1 for item in records if item["deadline_missed"])
        hazard_quality: dict[str, dict[str, int | float]] = {}
        opportunity_accounting = {item.value: 0 for item in OpportunityDisposition}
        opportunity_accounting["never_started"] = 0
        for item in records:
            opportunity_accounting[item["disposition"]] = opportunity_accounting.get(item["disposition"], 0) + 1
            row = hazard_quality.setdefault(item["hazard"], {"offered": 0, "processed": 0, "skipped": 0, "deadline_misses": 0})
            row["offered"] += 1
            row["processed"] += item["disposition"] == "processed"
            row["skipped"] += item["disposition"] == "skipped"
            row["deadline_misses"] += bool(item["deadline_missed"])
        opportunity_accounting["offered"] = len(records)
        for row in hazard_quality.values():
            row["completion_rate"] = row["processed"] / row["offered"] if row["offered"] else 0.0
        histogram_edges = (0.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0)
        counts = [0] * (len(histogram_edges) - 1)
        overflow = 0
        for value in end_to_end:
            index = next((i for i in range(len(histogram_edges) - 1) if histogram_edges[i] <= value < histogram_edges[i + 1]), None)
            if index is None:
                overflow += 1
            else:
                counts[index] += 1
        return BenchmarkRun(
            variant=variant,
            claim_class=ClaimClass.SIMULATED,
            schedule_digest=schedule_digest,
            offered=len(records),
            processed=sum(1 for item in records if item["disposition"] == "processed"),
            skipped=sum(1 for item in records if item["disposition"] == "skipped"),
            deadline_misses=misses,
            median_end_to_end_ms=statistics.median(end_to_end) if end_to_end else 0.0,
            p50_end_to_end_ms=_percentile(end_to_end, 0.50),
            p95_end_to_end_ms=_percentile(end_to_end, 0.95),
            p99_end_to_end_ms=_percentile(end_to_end, 0.99),
            latency_histogram={"metric": "end_to_end_ms", "edges": histogram_edges, "counts": tuple(counts), "precision_ms": 1.0, "range_policy": "overflow_not_clipped"},
            raw_latency_samples_ms=tuple(end_to_end),
            latency_overflow_count=overflow,
            resource_samples=(
                {"sample_index": 0, "model_size_bytes": int(manifest.get("model_size_bytes", 0)),
                 "rss_mb": float(manifest.get("resources", {}).get("rss_mb", 0.0)),
                 "cpu_pressure": float(manifest.get("resources", {}).get("cpu_pressure", 0.0)),
                 "temperature_c": float(manifest.get("resources", {}).get("temperature_c", 0.0)),
                 "source": "simulated_benchmark_resource_snapshot",
                 "evidence_class": "simulated",
                 "physical_measurement": False},
            ),
            total_service_ms=total_service_ms,
            total_queue_delay_ms=total_queue_delay_ms,
            heavy_model_invocation_count=len(heavy_records),
            heavy_model_service_ms=heavy_model_service_ms,
            heavy_model_duty_cycle=round(heavy_model_duty_cycle, 6),
            scheduler_decision_count=scheduler_decision_count,
            hazard_quality=hazard_quality,
            opportunity_accounting=opportunity_accounting,
            execution_mode="orchestrated" if variant is BenchmarkVariant.O1 else "fixed_rate",
            instrumentation_config_hashes=config_hashes,
            telemetry_policy_digest=telemetry_policy_digest,
            quality_scope="timed_run_only" if variant is BenchmarkVariant.O1 else "timed_run_replay",
            camera_preprocessing=dict(camera_preprocessing),
            records=tuple(records),
        )

    def _run_fixed(self, start: datetime, opportunities: list[BenchmarkOpportunity], variant: BenchmarkVariant) -> list[dict[str, Any]]:
        now_ms = 0
        records: list[dict[str, Any]] = []
        for item in sorted(opportunities, key=lambda value: value.scheduled_offset_ms):
            release_ms = item.scheduled_offset_ms
            service_start_ms = max(now_ms, release_ms)
            completion_ms = service_start_ms + item.service_ms[variant]
            now_ms = completion_ms
            end_to_end_ms = completion_ms - item.captured_offset_ms
            records.append(self._record(item, release_ms, service_start_ms, completion_ms, end_to_end_ms))
        return records

    def _run_orchestrated(
        self,
        start: datetime,
        opportunities: list[BenchmarkOpportunity],
        variant: BenchmarkVariant,
        resources_raw: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], int]:
        clock = VirtualClock(start)
        approved = {item.profile_id for item in opportunities}
        scheduler = WorkloadScheduler(clock=clock, mode=RuntimeMode.BENCHMARK, approved_profile_ids=approved)
        scheduler_decision_count = 0

        def scheduler_call(function, *args, **kwargs):
            nonlocal scheduler_decision_count
            result = function(*args, **kwargs)
            scheduler_decision_count += 1
            return result

        specs: dict[str, WorkloadSpec] = {}
        for item in opportunities:
            if item.workload_id not in specs:
                spec = WorkloadSpec(
                    workload_id=item.workload_id,
                    hazard=item.hazard,
                    tier=item.tier,
                    period_ms=max(1, item.deadline_ms),
                    deadline_ms=item.deadline_ms,
                    max_deferral_ms=item.max_deferral_ms,
                    estimated_cost_ms=item.service_ms[variant],
                    memory_mb=item.memory_mb,
                    profile_id=item.profile_id,
                )
                specs[item.workload_id] = spec
                scheduler_call(scheduler.register, spec)
        resources = ResourceSnapshot.model_validate(resources_raw or {
            "cpu_pressure": 0.4,
            "memory_pressure": 0.4,
            "io_pressure": 0.2,
            "temperature_c": 55.0,
            "available_memory_mb": 512,
            "power_degraded": False,
        })
        arrivals = list(sorted(enumerate(opportunities), key=lambda pair: (pair[1].scheduled_offset_ms, pair[0])))
        jobs_by_id: dict[UUID, tuple[BenchmarkOpportunity, int]] = {}
        records: list[dict[str, Any]] = []
        active: tuple[Any, BenchmarkOpportunity, int, int] | None = None

        def submit_due() -> None:
            now_ms = clock.monotonic_ns() // 1_000_000
            while arrivals and arrivals[0][1].scheduled_offset_ms <= now_ms:
                _, item = arrivals.pop(0)
                correlation_id = uuid5(NAMESPACE_URL, f"benchmark:{item.opportunity_key}")
                job = scheduler_call(scheduler.submit,
                    item.workload_id,
                    {"opportunity_key": item.opportunity_key},
                    released_at=start + timedelta(milliseconds=item.scheduled_offset_ms),
                    scheduled_release_at=start + timedelta(milliseconds=item.scheduled_offset_ms),
                    captured_at=start + timedelta(milliseconds=item.captured_offset_ms),
                    correlation_id=correlation_id,
                )
                jobs_by_id[job.job_id] = (item, item.scheduled_offset_ms)

        while arrivals or scheduler.queued or active is not None:
            if active is None and not scheduler.queued and arrivals:
                next_ms = arrivals[0][1].scheduled_offset_ms
                now_ms = clock.monotonic_ns() // 1_000_000
                if next_ms > now_ms:
                    clock.advance_ms(next_ms - now_ms)
            submit_due()
            if active is None:
                job = scheduler_call(scheduler.dispatch, resources)
                if job is None:
                    if scheduler.queued:
                        break
                    continue
                item, release_ms = jobs_by_id[job.job_id]
                service_start_ms = job.service_started_monotonic_ns // 1_000_000
                active = (job, item, release_ms, item.service_ms[variant])
            job, item, release_ms, remaining_ms = active
            now_ms = clock.monotonic_ns() // 1_000_000
            next_arrival_ms = arrivals[0][1].scheduled_offset_ms if arrivals else None
            if next_arrival_ms is not None and next_arrival_ms < now_ms + remaining_ms:
                delta = next_arrival_ms - now_ms
                clock.advance_ms(delta)
                active = (job, item, release_ms, remaining_ms - delta)
                submit_due()
                continue
            clock.advance_ms(remaining_ms)
            scheduler_call(scheduler.complete, job)
            completion_ms = job.completed_monotonic_ns // 1_000_000
            service_start_ms = job.service_started_monotonic_ns // 1_000_000
            end_to_end_ms = completion_ms - item.captured_offset_ms
            records.append(self._record(item, release_ms, service_start_ms, completion_ms, end_to_end_ms))
            active = None

        processed_keys = {record["opportunity_key"] for record in records}
        for item in opportunities:
            if item.opportunity_key not in processed_keys:
                records.append({
                    **self._record(item, item.scheduled_offset_ms, None, None, None),
                    "disposition": "skipped",
                    "reason_codes": ["not_dispatched"],
                    "deadline_missed": True,
                })
        return (
            sorted(records, key=lambda value: (value["service_start_ms"] is None, value["service_start_ms"] or 0, value["opportunity_key"])),
            scheduler_decision_count,
        )

    @staticmethod
    def _record(
        item: BenchmarkOpportunity,
        release_ms: int,
        service_start_ms: int | None,
        completion_ms: int | None,
        end_to_end_ms: int | None,
    ) -> dict[str, Any]:
        deadline_at_ms = release_ms + item.deadline_ms
        return {
            "opportunity_key": item.opportunity_key,
            "workload_id": item.workload_id,
            "hazard": item.hazard.value,
            "tier": int(item.tier),
            "scheduled_release_ms": item.scheduled_offset_ms,
            "actual_release_ms": release_ms,
            "capture_ms": item.captured_offset_ms,
            "queue_start_ms": release_ms,
            "service_start_ms": service_start_ms,
            "completion_ms": completion_ms,
            "queue_latency_ms": None if service_start_ms is None else service_start_ms - release_ms,
            "service_ms": None if completion_ms is None or service_start_ms is None else completion_ms - service_start_ms,
            "stage_latency_ms": None if completion_ms is None or service_start_ms is None else {
                "decode": (completion_ms - service_start_ms) // 5,
                "preprocess": (completion_ms - service_start_ms) // 5,
                "infer": (completion_ms - service_start_ms) * 2 // 5,
                "postprocess": (completion_ms - service_start_ms) // 10,
                "store": (completion_ms - service_start_ms) - ((completion_ms - service_start_ms) // 5) * 2 - ((completion_ms - service_start_ms) * 2 // 5) - ((completion_ms - service_start_ms) // 10),
            },
            "end_to_end_ms": end_to_end_ms,
            "deadline_ms": item.deadline_ms,
            "deadline_missed": completion_ms is None or completion_ms > deadline_at_ms,
            "disposition": "processed" if completion_ms is not None else "skipped",
            "reason_codes": [],
        }


def load_benchmark_manifest(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
