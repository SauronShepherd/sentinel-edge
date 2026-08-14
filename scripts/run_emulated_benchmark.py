from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable
from uuid import NAMESPACE_URL, uuid5

from sentinel_edge.benchmark import DeterministicBenchmarkLab, load_benchmark_manifest
from sentinel_edge.domain.models import (
    BenchmarkVariant,
    CriticalityTier,
    HazardKind,
    ResourceSnapshot,
    RuntimeMode,
    WorkloadSpec,
)
from sentinel_edge.runtime import VirtualClock, WorkloadScheduler
from sentinel_edge.security import sha256_file
from sentinel_edge.qualification.arm64_network import inspect_container_network
from sentinel_edge.qualification.arm64_runtime import EXPECTED_ORT_VERSION, run_onnxruntime_known_answer

try:  # ``resource`` is available in the Linux Arm64 guest, not on Windows hosts.
    import resource
except ImportError:  # pragma: no cover - exercised by host-only test collection
    resource = None

ROOT = Path(__file__).resolve().parents[1]


def max_rss_kb() -> int:
    """Return the guest RSS receipt when the platform exposes ``resource``."""
    if resource is None:
        return 0
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def measure_scheduler_overhead(manifest: dict, *, iterations: int = 50) -> dict:
    """Measure Component-3 Python scheduler decision overhead inside the Arm64 guest.

    This is deliberately separate from the deterministic semantic service-time model.
    The result is an emulator-execution observation, not Raspberry Pi hardware timing.
    """
    if iterations < 1:
        raise ValueError("iterations must be positive")
    start = datetime.fromisoformat(str(manifest["start_at"]).replace("Z", "+00:00"))
    opportunities = list(manifest["opportunities"])
    approved = {str(item["profile_id"]) for item in opportunities}
    resources = ResourceSnapshot.model_validate(manifest.get("resources") or {
        "cpu_pressure": 0.4,
        "memory_pressure": 0.4,
        "io_pressure": 0.2,
        "temperature_c": 55.0,
        "available_memory_mb": 512,
        "power_degraded": False,
    })
    samples_us: list[float] = []
    decision_count = 0

    def timed_call(function: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        nonlocal decision_count
        before = time.process_time_ns()
        result = function(*args, **kwargs)
        samples_us.append((time.process_time_ns() - before) / 1_000.0)
        decision_count += 1
        return result

    for iteration in range(iterations):
        clock = VirtualClock(start)
        scheduler = WorkloadScheduler(
            clock=clock,
            mode=RuntimeMode.BENCHMARK,
            approved_profile_ids=approved,
        )
        registered: set[str] = set()
        for item in opportunities:
            workload_id = str(item["workload_id"])
            if workload_id in registered:
                continue
            service_ms = int(item["service_ms"]["O1"])
            spec = WorkloadSpec(
                workload_id=workload_id,
                hazard=HazardKind(str(item["hazard"])),
                tier=CriticalityTier(int(item["tier"])),
                period_ms=max(1, int(item["deadline_ms"])),
                deadline_ms=int(item["deadline_ms"]),
                max_deferral_ms=int(item["max_deferral_ms"]),
                estimated_cost_ms=service_ms,
                memory_mb=int(item["memory_mb"]),
                profile_id=str(item["profile_id"]),
            )
            timed_call(scheduler.register, spec)
            registered.add(workload_id)

        jobs: dict[object, dict] = {}
        for item in sorted(opportunities, key=lambda row: (int(row["scheduled_offset_ms"]), str(row["opportunity_key"]))):
            offset = int(item["scheduled_offset_ms"] )
            now_ms = clock.monotonic_ns() // 1_000_000
            if offset > now_ms:
                clock.advance_ms(offset - now_ms)
            correlation_id = uuid5(NAMESPACE_URL, f"scheduler-overhead:{iteration}:{item['opportunity_key']}")
            job = timed_call(
                scheduler.submit,
                str(item["workload_id"]),
                {"opportunity_key": item["opportunity_key"]},
                released_at=start + timedelta(milliseconds=offset),
                scheduled_release_at=start + timedelta(milliseconds=offset),
                captured_at=start + timedelta(milliseconds=int(item["captured_offset_ms"])),
                correlation_id=correlation_id,
            )
            jobs[job.job_id] = item

        safety = 0
        while scheduler.queued:
            safety += 1
            if safety > len(opportunities) * 4:
                raise RuntimeError("scheduler overhead microbenchmark failed to drain queue")
            job = timed_call(scheduler.dispatch, resources)
            if job is None:
                clock.advance_ms(1)
                continue
            item = jobs[job.job_id]
            clock.advance_ms(int(item["service_ms"]["O1"]))
            timed_call(scheduler.complete, job)

    total_cpu_ms = sum(samples_us) / 1000.0
    return {
        "measurement_class": "measured_emulated_arm64",
        "scope": "component_3_scheduler_python_control_plane",
        "iterations": iterations,
        "decision_count": decision_count,
        "total_cpu_ms": round(total_cpu_ms, 6),
        "median_per_decision_us": round(statistics.median(samples_us), 6),
        "p95_per_decision_us": round(sorted(samples_us)[max(0, min(len(samples_us) - 1, int(len(samples_us) * 0.95) - 1))], 6),
        "max_per_decision_us": round(max(samples_us), 6),
        "note": "Measured in the emulated AArch64 guest; not Raspberry Pi 5 scheduler timing.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="fixtures/scenarios/benchmark-open-loop.json")
    parser.add_argument("--output", default="qualification/emulated-arm64-benchmark.json")
    args = parser.parse_args()
    manifest_path = ROOT / args.manifest
    output_path = ROOT / args.output
    machine = platform.machine().lower()
    if machine not in {"aarch64", "arm64"}:
        print(json.dumps({"valid": False, "reason": "arm64_guest_required", "observed": machine}, sort_keys=True))
        return 2

    try:
        import onnxruntime as ort
        ort_identity = {"version": ort.__version__, "providers": list(ort.get_available_providers())}
    except Exception as exc:  # pragma: no cover - guest diagnostic
        print(json.dumps({"valid": False, "reason": "onnxruntime_unavailable", "error": str(exc)}, sort_keys=True))
        return 2
    if ort_identity["version"] != EXPECTED_ORT_VERSION:
        print(json.dumps({"valid": False, "reason": "onnxruntime_version_mismatch", "observed": ort_identity["version"], "expected": EXPECTED_ORT_VERSION}, sort_keys=True))
        return 2
    if "CPUExecutionProvider" not in ort_identity["providers"]:
        print(json.dumps({"valid": False, "reason": "cpu_execution_provider_missing", "providers": ort_identity["providers"]}, sort_keys=True))
        return 2

    known_answer = run_onnxruntime_known_answer(ROOT, ort_module=ort)
    if known_answer.get("passed") is not True:
        print(json.dumps({"valid": False, "reason": "onnxruntime_known_answer_failed", "known_answer": known_answer}, sort_keys=True))
        return 2

    network_isolation = inspect_container_network()
    if network_isolation["valid"] is not True:
        print(json.dumps({"valid": False, "reason": "arm64_guest_network_not_isolated", "network_isolation": network_isolation}, sort_keys=True))
        return 2

    manifest = load_benchmark_manifest(manifest_path)
    lab = DeterministicBenchmarkLab()
    policy = manifest["benchmark_policy"]
    repeats = int(policy["repeats"])
    warmups = int(policy["warmup_runs"])
    results = {}
    schedule_digests = set()
    for variant in BenchmarkVariant:
        for _ in range(warmups):
            lab.run(manifest, variant)
        wall_samples = []
        cpu_samples = []
        semantic_run = None
        for _ in range(repeats):
            wall_start = time.perf_counter_ns()
            cpu_start = time.process_time_ns()
            semantic_run = lab.run(manifest, variant)
            cpu_samples.append((time.process_time_ns() - cpu_start) / 1_000_000)
            wall_samples.append((time.perf_counter_ns() - wall_start) / 1_000_000)
        assert semantic_run is not None
        schedule_digests.add(semantic_run.schedule_digest)
        results[variant.value] = {
            "semantic": semantic_run.model_dump(mode="json"),
            "emulator_execution": {
                "wall_ms": wall_samples,
                "wall_median_ms": statistics.median(wall_samples),
                "cpu_ms": cpu_samples,
                "cpu_median_ms": statistics.median(cpu_samples),
                "max_rss_kb": max_rss_kb(),
            },
        }

    b0 = results["B0"]["semantic"]
    b1 = results["B1"]["semantic"]
    o1 = results["O1"]["semantic"]
    earthquake_o1 = o1["hazard_quality"].get("earthquake", {})
    scheduler_overhead = measure_scheduler_overhead(manifest)
    quality_checks = {
        "arm64_guest_network_isolated": network_isolation["valid"] is True,
        "runtime_known_answer_passed": known_answer.get("passed") is True,
        "runtime_provider_assignment_cpu_only": known_answer.get("assigned_providers") == ["CPUExecutionProvider"],
        "runtime_distribution_identity_bound": bool(known_answer.get("runtime_distribution", {}).get("record_sha256")) and bool(known_answer.get("runtime_distribution", {}).get("native_files")),
        "scheduler_overhead_measured_in_arm64_guest": scheduler_overhead.get("measurement_class") == "measured_emulated_arm64" and scheduler_overhead.get("decision_count", 0) > 0,
        "semantic_resource_samples_explicitly_simulated": all(
            row.get("resource_samples") and row["resource_samples"][0].get("evidence_class") == "simulated" and row["resource_samples"][0].get("physical_measurement") is False
            for row in (b0, b1, o1)
        ),
        "semantic_workload_metrics_present": all(
            {"total_service_ms", "total_queue_delay_ms", "heavy_model_invocation_count", "heavy_model_duty_cycle", "scheduler_decision_count"} <= set(row)
            for row in (b0, b1, o1)
        ),
        "same_opportunity_schedule": len(schedule_digests) == 1,
        "all_variants_offer_same_count": len({b0["offered"], b1["offered"], o1["offered"]}) == 1,
        "all_opportunities_processed": all(row["processed"] == row["offered"] for row in (b0, b1, o1)),
        "model_runtime_optimization_not_worse_than_baseline": b1["median_end_to_end_ms"] <= b0["median_end_to_end_ms"],
        "orchestrator_not_worse_than_b1": o1["median_end_to_end_ms"] <= b1["median_end_to_end_ms"],
        "orchestrator_deadline_misses_not_worse_than_b1": o1["deadline_misses"] <= b1["deadline_misses"],
        "tier_a_earthquake_deadline_preserved_in_o1": earthquake_o1.get("deadline_misses") == 0,
    }
    quality_guardrails_passed = all(quality_checks.values())
    payload = {
        "schema": "sentinel-edge.emulated-arm64-benchmark.v1",
        "release_profile": "H0-EMULATED-AARCH64-20260813",
        "claim_class": "simulated",
        "environment": {
            "guest_architecture": platform.machine(),
            "host_architecture": os.environ.get("SENTINEL_HOST_ARCH"),
            "execution_mode": "docker-qemu-linux-arm64",
            "container_image": {
                "ref": os.environ.get("SENTINEL_ARM64_IMAGE_REF"),
                "id": os.environ.get("SENTINEL_ARM64_IMAGE_ID"),
            },
            "python": platform.python_version(),
            "onnxruntime": ort_identity,
            "known_answer_inference": known_answer,
            "network_isolation": network_isolation,
        },
        "manifest": {"path": args.manifest, "sha256": sha256_file(manifest_path)},
        "instrumentation": {
            "scheduler_overhead": scheduler_overhead,
            "semantic_resource_policy": {
                "evidence_class": "simulated",
                "physical_measurement": False,
                "fields": ["cpu_pressure", "memory_pressure", "io_pressure", "temperature_c", "power_degraded"],
            },
        },
        "quality_checks": quality_checks,
        "quality_guardrails_passed": quality_guardrails_passed,
        "results": results,
        "comparisons": {
            "B0_to_B1_median_end_to_end_ms_delta": b1["median_end_to_end_ms"] - b0["median_end_to_end_ms"],
            "B1_to_O1_median_end_to_end_ms_delta": o1["median_end_to_end_ms"] - b1["median_end_to_end_ms"],
            "B0_to_O1_median_end_to_end_ms_delta": o1["median_end_to_end_ms"] - b0["median_end_to_end_ms"],
            "B0_to_B1_deadline_miss_delta": b1["deadline_misses"] - b0["deadline_misses"],
            "B1_to_O1_deadline_miss_delta": o1["deadline_misses"] - b1["deadline_misses"],
            "B0_to_B1_total_service_ms_delta": b1["total_service_ms"] - b0["total_service_ms"],
            "B1_to_O1_total_service_ms_delta": o1["total_service_ms"] - b1["total_service_ms"],
            "B0_to_O1_total_queue_delay_ms_delta": o1["total_queue_delay_ms"] - b0["total_queue_delay_ms"],
            "heavy_model_invocation_count": {"B0": b0["heavy_model_invocation_count"], "B1": b1["heavy_model_invocation_count"], "O1": o1["heavy_model_invocation_count"]},
            "heavy_model_duty_cycle": {"B0": b0["heavy_model_duty_cycle"], "B1": b1["heavy_model_duty_cycle"], "O1": o1["heavy_model_duty_cycle"]},
        },
        "limitations": [
            "All hazard opportunities, semantic service times, and thermal/power/resource-pressure inputs are deterministic simulations.",
            "Wall/CPU/RSS values and scheduler-overhead timing describe the Arm64-emulated guest process, not Raspberry Pi 5 performance.",
            "No physical energy, thermal, throttling, power, or sensor-quality claim is made.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if quality_guardrails_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
