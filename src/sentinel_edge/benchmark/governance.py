from __future__ import annotations

import base64
import json
import math
import random
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel_edge.domain.models import BenchmarkVariant, ClaimClass
from sentinel_edge.qualification.power_energy import (
    EnergyMeasurement,
    PowerTelemetrySample,
    benchmark_invalidation_reasons,
    evaluate_energy_comparison,
)
from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file
from sentinel_edge.update import key_id


class BenchmarkIdentitySet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    runtime_profile_sha256s: tuple[str, ...]
    model_sha256s: tuple[str, ...]
    configuration_sha256: str
    fixture_manifest_sha256: str
    opportunity_manifest_sha256: str
    host_report_sha256: str
    network_isolation_report_sha256: str
    wheelhouse_report_sha256: str

    @model_validator(mode="after")
    def nonempty(self) -> "BenchmarkIdentitySet":
        values = self.model_dump(mode="json")
        for name, value in values.items():
            if isinstance(value, list):
                if not value or any(len(str(item)) != 64 for item in value):
                    raise ValueError(f"{name} must contain SHA-256 digests")
            elif len(str(value)) != 64:
                raise ValueError(f"{name} must be a SHA-256 digest")
        return self


class BenchmarkAnalysisPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True)

    schema_: Literal["sentinel-edge-benchmark-analysis-plan/1.0"] = Field(default="sentinel-edge-benchmark-analysis-plan/1.0", alias="schema")
    plan_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    created_at: datetime
    claim_set: Literal["confirmatory", "exploratory"]
    primary_metrics: tuple[str, ...] = Field(min_length=1)
    guardrails: dict[str, float]
    exclusions: tuple[str, ...]
    interval_method: Literal["paired_percentile_bootstrap"] = "paired_percentile_bootstrap"
    confidence_level: float = Field(gt=0.5, lt=1.0)
    bootstrap_resamples: int = Field(ge=100, le=100_000)
    variants: tuple[BenchmarkVariant, ...]
    minimum_complete_pairs: int = Field(ge=2)
    stop_rule: dict[str, Any]
    offered_load_manifest_sha256: str = Field(min_length=64, max_length=64)
    identities: BenchmarkIdentitySet

    @model_validator(mode="after")
    def exact_variants(self) -> "BenchmarkAnalysisPlan":
        if tuple(self.variants) != (BenchmarkVariant.B0, BenchmarkVariant.B1, BenchmarkVariant.O1):
            raise ValueError("variants must be ordered exactly B0, B1, O1")
        if not self.stop_rule.get("type"):
            raise ValueError("stop_rule.type is required")
        if not self.campaign_id.strip():
            raise ValueError("campaign_id is required")
        return self


class SignedBenchmarkPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True)

    schema_: Literal["sentinel-edge-signed-benchmark-plan/1.0"] = Field(default="sentinel-edge-signed-benchmark-plan/1.0", alias="schema")
    plan: BenchmarkAnalysisPlan
    plan_sha256: str
    signer_key_id: str
    signed_at: datetime
    algorithm: Literal["Ed25519"] = "Ed25519"
    signature_b64: str


class BenchmarkSample(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    block_index: int = Field(ge=0)
    pair_id: str = Field(min_length=1)
    opportunity_key: str = Field(min_length=1)
    variant: BenchmarkVariant
    metrics: dict[str, float]
    excluded: bool = False
    invalidation_reasons: tuple[str, ...] = ()
    platform: PowerTelemetrySample | None = None
    energy: EnergyMeasurement | None = None

    @model_validator(mode="after")
    def exclusion_reason(self) -> "BenchmarkSample":
        if self.excluded and not self.invalidation_reasons:
            raise ValueError("excluded samples require an invalidation reason")
        return self


class BenchmarkExecutionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True)

    schema_: Literal["sentinel-edge-benchmark-execution/1.0"] = Field(default="sentinel-edge-benchmark-execution/1.0", alias="schema")
    run_id: str
    plan_sha256: str
    started_at: datetime
    completed_at: datetime
    source_class: ClaimClass
    identities: BenchmarkIdentitySet
    observed_network_attempts: int = Field(ge=0)
    mutation_attempts: tuple[str, ...] = ()
    samples: tuple[BenchmarkSample, ...]
    declared_target_run: bool = False


class FileIdentitySpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    path: str
    sha256: str = Field(min_length=64, max_length=64)


def sign_analysis_plan(plan: BenchmarkAnalysisPlan, private_key: Ed25519PrivateKey, *, signed_at: datetime | None = None) -> SignedBenchmarkPlan:
    plan_bytes = canonical_json_bytes(plan.model_dump(mode="json"))
    return SignedBenchmarkPlan(
        plan=plan,
        plan_sha256=sha256_bytes(plan_bytes),
        signer_key_id=key_id(private_key.public_key()),
        signed_at=signed_at or datetime.now(timezone.utc),
        signature_b64=base64.b64encode(private_key.sign(plan_bytes)).decode("ascii"),
    )


def verify_signed_plan(envelope: SignedBenchmarkPlan | dict[str, Any], public_key: Ed25519PublicKey) -> dict[str, Any]:
    signed = envelope if isinstance(envelope, SignedBenchmarkPlan) else SignedBenchmarkPlan.model_validate(envelope)
    plan_bytes = canonical_json_bytes(signed.plan.model_dump(mode="json"))
    failures: list[str] = []
    if sha256_bytes(plan_bytes) != signed.plan_sha256:
        failures.append("plan_digest_mismatch")
    if key_id(public_key) != signed.signer_key_id:
        failures.append("plan_signer_key_mismatch")
    try:
        public_key.verify(base64.b64decode(signed.signature_b64, validate=True), plan_bytes)
    except (ValueError, InvalidSignature):
        failures.append("plan_signature_invalid")
    if signed.signed_at < signed.plan.created_at:
        failures.append("plan_signed_before_creation")
    return {
        "schema": "sentinel-edge-benchmark-plan-verification/1.0",
        "valid": not failures,
        "plan_sha256": signed.plan_sha256,
        "claim_set": signed.plan.claim_set,
        "failures": failures,
    }


def verify_file_identities(root: str | Path, specs: tuple[FileIdentitySpec, ...]) -> dict[str, Any]:
    root_path = Path(root).resolve()
    records: list[dict[str, Any]] = []
    failures: list[str] = []
    for spec in specs:
        path = (root_path / spec.path).resolve()
        try:
            path.relative_to(root_path)
        except ValueError:
            records.append({"name": spec.name, "path": spec.path, "match": False, "reason": "path_outside_root"})
            failures.append(f"identity_path_outside_root:{spec.name}")
            continue
        observed = sha256_file(path) if path.is_file() else None
        match = observed == spec.sha256
        records.append({"name": spec.name, "path": spec.path, "expected_sha256": spec.sha256, "observed_sha256": observed, "match": match})
        if not match:
            failures.append(f"identity_mismatch:{spec.name}")
    base = {
        "schema": "sentinel-edge-benchmark-identity-verification/1.0",
        "records": records,
        "measured_mode_allowed": not failures,
        "failures": failures,
    }
    return {**base, "report_digest": sha256_bytes(canonical_json_bytes(base))}


def _bootstrap_interval(values: list[float], *, confidence: float, resamples: int, seed_material: str) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    if len(values) == 1:
        return (values[0], values[0])
    rng = random.Random(int(seed_material[:16], 16))
    means: list[float] = []
    for _ in range(resamples):
        means.append(statistics.fmean(rng.choice(values) for _ in values))
    means.sort()
    tail = (1.0 - confidence) / 2.0
    low_index = max(0, min(len(means) - 1, math.floor(tail * len(means))))
    high_index = max(0, min(len(means) - 1, math.ceil((1.0 - tail) * len(means)) - 1))
    return (means[low_index], means[high_index])


def _alternation_failures(samples: tuple[BenchmarkSample, ...]) -> list[str]:
    active = sorted((sample for sample in samples if not sample.excluded), key=lambda sample: sample.block_index)
    seen_indices: set[int] = set()
    failures: list[str] = []
    for sample in active:
        if sample.block_index in seen_indices:
            failures.append("duplicate_block_index")
        seen_indices.add(sample.block_index)
        expected = (BenchmarkVariant.B0, BenchmarkVariant.B1, BenchmarkVariant.O1)[sample.block_index % 3]
        if sample.variant is not expected:
            failures.append(f"alternation_violation:{sample.block_index}")
    if seen_indices and seen_indices != set(range(min(seen_indices), max(seen_indices) + 1)):
        failures.append("block_index_gap")
    return sorted(set(failures))


def analyze_execution(
    signed_plan: SignedBenchmarkPlan | dict[str, Any],
    public_key: Ed25519PublicKey,
    execution: BenchmarkExecutionRecord | dict[str, Any],
    *,
    network_report: dict[str, Any],
    host_report: dict[str, Any],
    runtime_qualifications: tuple[dict[str, Any], ...],
    wheelhouse_report: dict[str, Any],
) -> dict[str, Any]:
    signed = signed_plan if isinstance(signed_plan, SignedBenchmarkPlan) else SignedBenchmarkPlan.model_validate(signed_plan)
    run = execution if isinstance(execution, BenchmarkExecutionRecord) else BenchmarkExecutionRecord.model_validate(execution)
    plan_verification = verify_signed_plan(signed, public_key)
    failures: list[str] = list(plan_verification["failures"])
    invalidations: list[dict[str, Any]] = []
    attempted_candidates = [
        {
            "block_index": sample.block_index,
            "pair_id": sample.pair_id,
            "opportunity_key": sample.opportunity_key,
            "variant": sample.variant.value,
            "status": "invalid" if sample.excluded else "attempted",
            "reason_codes": list(sample.invalidation_reasons),
        }
        for sample in run.samples
    ]
    if run.plan_sha256 != signed.plan_sha256:
        failures.append("execution_plan_digest_mismatch")
    if signed.signed_at >= run.started_at:
        failures.append("analysis_plan_not_frozen_before_run")
    if run.identities != signed.plan.identities:
        failures.append("execution_identity_set_mismatch")
    if signed.plan.offered_load_manifest_sha256 != run.identities.opportunity_manifest_sha256:
        failures.append("offered_load_identity_mismatch")
    if run.observed_network_attempts:
        failures.append("network_attempt_observed")
    if run.mutation_attempts:
        failures.append("benchmark_mutation_attempted")
    failures.extend(_alternation_failures(run.samples))
    effective_reasons: dict[int, tuple[str, ...]] = {}
    max_memory_psi = float(signed.plan.guardrails.get("max_memory_psi_avg10", 10.0))
    max_major_faults = int(signed.plan.guardrails.get("max_major_faults_delta", 0.0))
    for sample in run.samples:
        reasons = list(sample.invalidation_reasons)
        if sample.platform is not None:
            reasons.extend(benchmark_invalidation_reasons(
                sample.platform,
                maximum_memory_psi_avg10=max_memory_psi,
                maximum_major_faults_delta=max_major_faults,
            ))
        if sample.energy is not None and not sample.energy.quality_guardrail_passed:
            reasons.append("quality_guardrail_failed")
        effective_reasons[sample.block_index] = tuple(sorted(set(reasons)))
        if sample.excluded or reasons:
            invalidations.append({
                "block_index": sample.block_index,
                "pair_id": sample.pair_id,
                "opportunity_key": sample.opportunity_key,
                "variant": sample.variant.value,
                "reason_codes": list(effective_reasons[sample.block_index]),
                "declared_excluded": sample.excluded,
            })
    if network_report.get("below_application_layer_proven") is not True or network_report.get("release_eligible") is not True:
        failures.append("qualified_network_isolation_missing")
    if sha256_bytes(canonical_json_bytes({k: v for k, v in network_report.items() if k != "report_digest"})) != network_report.get("report_digest"):
        failures.append("network_isolation_report_digest_mismatch")
    if host_report.get("target_device_claim_allowed") is not True:
        failures.append("target_host_not_qualified")
    if sha256_bytes(canonical_json_bytes(host_report)) != signed.plan.identities.host_report_sha256:
        failures.append("host_report_identity_mismatch")
    runtime_target = bool(runtime_qualifications) and all(item.get("target_qualified") is True for item in runtime_qualifications)
    observed_runtime_digests = tuple(sorted(sha256_bytes(canonical_json_bytes(item)) for item in runtime_qualifications))
    if observed_runtime_digests != tuple(sorted(signed.plan.identities.runtime_profile_sha256s)):
        failures.append("runtime_profile_identity_mismatch")
    if not runtime_target:
        failures.append("runtime_profiles_not_target_qualified")
    if wheelhouse_report.get("target_platform_complete") is not True:
        failures.append("target_wheelhouse_incomplete")
    if wheelhouse_report.get("report_digest") != signed.plan.identities.wheelhouse_report_sha256:
        failures.append("wheelhouse_report_identity_mismatch")

    active = [sample for sample in run.samples if not sample.excluded and not effective_reasons.get(sample.block_index)]
    by_pair: dict[str, dict[BenchmarkVariant, BenchmarkSample]] = {}
    for sample in active:
        by_pair.setdefault(sample.pair_id, {})[sample.variant] = sample
    complete_pairs = {pair_id: values for pair_id, values in by_pair.items() if set(values) == set(BenchmarkVariant)}
    if len(complete_pairs) < signed.plan.minimum_complete_pairs:
        failures.append("insufficient_complete_pairs")

    metrics: dict[str, Any] = {}
    for metric in signed.plan.primary_metrics:
        absolute = {variant.value: [] for variant in BenchmarkVariant}
        deltas = {"B1_minus_B0": [], "O1_minus_B1": [], "O1_minus_B0": []}
        for values in complete_pairs.values():
            if not all(metric in values[variant].metrics for variant in BenchmarkVariant):
                continue
            b0 = values[BenchmarkVariant.B0].metrics[metric]
            b1 = values[BenchmarkVariant.B1].metrics[metric]
            o1 = values[BenchmarkVariant.O1].metrics[metric]
            absolute["B0"].append(b0); absolute["B1"].append(b1); absolute["O1"].append(o1)
            deltas["B1_minus_B0"].append(b1 - b0)
            deltas["O1_minus_B1"].append(o1 - b1)
            deltas["O1_minus_B0"].append(o1 - b0)
        metric_result: dict[str, Any] = {
            "pair_count": min((len(values) for values in absolute.values()), default=0),
            "absolute": {
                variant: {
                    "mean": statistics.fmean(values) if values else None,
                    "median": statistics.median(values) if values else None,
                    "sample_count": len(values),
                }
                for variant, values in absolute.items()
            },
            "paired_deltas": {},
        }
        for name, values in deltas.items():
            interval = _bootstrap_interval(values, confidence=signed.plan.confidence_level, resamples=signed.plan.bootstrap_resamples, seed_material=signed.plan_sha256 + metric + name)
            baseline_values = absolute["B0"] if name in {"B1_minus_B0", "O1_minus_B0"} else absolute["B1"]
            baseline_mean = statistics.fmean(baseline_values) if baseline_values else 0.0
            scale = statistics.pstdev(baseline_values) if len(baseline_values) > 1 else 0.0
            effect = (statistics.fmean(values) / scale) if values and scale > 0 else None
            delta_mean = statistics.fmean(values) if values else None
            metric_result["paired_deltas"][name] = {
                "mean": delta_mean,
                "percentage_delta": (delta_mean / baseline_mean * 100.0) if delta_mean is not None and baseline_mean else None,
                "confidence_interval": list(interval) if values else None,
                "confidence_level": signed.plan.confidence_level,
                "effect_size_standardized": effect,
                "sample_count": len(values),
            }
        metrics[metric] = metric_result

    energy_items = tuple(sample.energy for sample in active if sample.energy is not None)
    energy_comparison = evaluate_energy_comparison(energy_items) if energy_items else None
    if any(metric in {"energy_j", "energy_mj"} for metric in signed.plan.primary_metrics):
        if len(energy_items) != len(active):
            failures.append("energy_evidence_missing_for_active_sample")
        elif energy_comparison and energy_comparison.get("failures"):
            failures.extend(energy_comparison["failures"])
        if signed.plan.guardrails.get("physical_energy_required", 0.0) >= 1.0 and (
            not energy_comparison or energy_comparison.get("physical_energy_reportable") is not True
        ):
            failures.append("physical_energy_required_not_proven")

    platform_items = tuple(sample.platform for sample in run.samples if sample.platform is not None)
    platform_summary = {
        "sample_count": len(platform_items),
        "current_under_voltage_count": sum(item.under_voltage_current for item in platform_items),
        "current_frequency_cap_count": sum(item.frequency_capped_current for item in platform_items),
        "current_throttling_count": sum(item.throttled_current for item in platform_items),
        "historical_power_event_count": sum(item.history_power_event for item in platform_items),
        "swap_use_count": sum(item.swap_used_mb > 0 for item in platform_items),
        "major_faults_total": sum(item.major_faults_delta for item in platform_items),
        "maximum_memory_psi_avg10": max((item.memory_psi_avg10 for item in platform_items), default=0.0),
    }

    source_measured = run.source_class is ClaimClass.MEASURED
    if not source_measured:
        failures.append("source_not_measured")
    confirmatory = signed.plan.claim_set == "confirmatory"
    headline_eligible = confirmatory and not failures and source_measured and run.declared_target_run
    base = {
        "schema": "sentinel-edge-benchmark-analysis-report/1.0",
        "run_id": run.run_id,
        "plan_sha256": signed.plan_sha256,
        "claim_set": signed.plan.claim_set,
        "confirmatory": confirmatory,
        "source_class": run.source_class.value,
        "declared_target_run": run.declared_target_run,
        "targets": {"source": "signed_analysis_plan.guardrails", "values": dict(signed.plan.guardrails), "preclaimed_result_values": False},
        "results": {"source": "observed_execution_samples", "metrics": metrics},
        "complete_pair_count": len(complete_pairs),
        "sample_count": len(run.samples),
        "metrics": metrics,
        "platform_health": platform_summary,
        "energy_evidence": energy_comparison,
        "invalidations": invalidations,
        "attempted_candidates": attempted_candidates,
        "failures": sorted(set(failures)),
        "headline_eligible": headline_eligible,
        "target_measurement_claim_allowed": headline_eligible,
        "limitations": [
            "Exploratory output is never eligible for a frozen headline claim.",
            "A valid analysis contract does not substitute for target-host, runtime, network, thermal, power, or physical-signal qualification.",
        ],
    }
    return {**base, "report_digest": sha256_bytes(canonical_json_bytes(base))}


def verify_analysis_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    failures: list[str] = []
    if payload.get("schema") != "sentinel-edge-benchmark-analysis-report/1.0":
        failures.append("analysis_report_schema_mismatch")
    claimed = payload.get("report_digest")
    base = {key: value for key, value in payload.items() if key != "report_digest"}
    if claimed != sha256_bytes(canonical_json_bytes(base)):
        failures.append("analysis_report_digest_mismatch")
    if payload.get("claim_set") == "exploratory" and payload.get("headline_eligible"):
        failures.append("exploratory_report_marked_headline_eligible")
    return {
        "valid": not failures,
        "headline_eligible": bool(payload.get("headline_eligible")) and not failures,
        "target_measurement_claim_allowed": bool(payload.get("target_measurement_claim_allowed")) and not failures,
        "failures": failures,
    }
