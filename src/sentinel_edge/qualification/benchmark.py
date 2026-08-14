from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sentinel_edge.domain.models import BenchmarkEvidenceReport, BenchmarkVariant, ClaimClass
from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file


def validate_benchmark_evidence(
    path: str | Path,
    *,
    expected_manifest_sha256: str | None = None,
    expected_host_report_sha256: str | None = None,
) -> BenchmarkEvidenceReport:
    source = Path(path)
    payload: dict[str, Any] = json.loads(source.read_text(encoding="utf-8"))
    if payload.get("schema") != "sentinel-edge-target-benchmark-evidence/1.0":
        raise ValueError("unsupported benchmark evidence schema")
    reasons: list[str] = []
    manifest_sha = str(payload.get("benchmark_manifest_sha256", ""))
    host_sha = str(payload.get("host_report_sha256", ""))
    if expected_manifest_sha256 and manifest_sha != expected_manifest_sha256:
        reasons.append("benchmark_manifest_mismatch")
    if expected_host_report_sha256 and host_sha != expected_host_report_sha256:
        reasons.append("host_report_mismatch")
    samples = payload.get("samples", [])
    variants = tuple(BenchmarkVariant(value) for value in payload.get("variants", []))
    if set(variants) != set(BenchmarkVariant):
        reasons.append("variant_set_incomplete")
    opportunity_digests = {str(item.get("opportunity_manifest_sha256", "")) for item in samples}
    opportunity_equal = len(opportunity_digests) == 1 and "" not in opportunity_digests
    if not opportunity_equal:
        reasons.append("opportunity_manifest_not_equal")
    quality = bool(payload.get("quality_guardrails_passed", False))
    thermal = bool(payload.get("thermal_valid", False))
    power = bool(payload.get("power_valid", False))
    host_qualified = bool(payload.get("target_host_qualified", False))
    if not quality:
        reasons.append("quality_guardrails_failed")
    if not thermal:
        reasons.append("thermal_invalid")
    if not power:
        reasons.append("power_invalid")
    if not host_qualified:
        reasons.append("target_host_not_qualified")
    if not samples:
        reasons.append("raw_samples_missing")
    source_class = ClaimClass(payload.get("source_class", "simulated"))
    if source_class is not ClaimClass.MEASURED:
        reasons.append("source_not_measured")
    allowed = not reasons and source_class is ClaimClass.MEASURED
    return BenchmarkEvidenceReport(
        benchmark_id=str(payload.get("benchmark_id", "unnamed")),
        benchmark_manifest_sha256=manifest_sha,
        host_report_sha256=host_sha,
        runtime_profile_sha256s=tuple(sorted(str(value) for value in payload.get("runtime_profile_sha256s", []))),
        source_class=source_class,
        variants=variants,
        raw_sample_count=len(samples),
        opportunity_manifest_equal=opportunity_equal,
        quality_guardrails_passed=quality,
        thermal_valid=thermal,
        power_valid=power,
        target_host_qualified=host_qualified,
        target_measurement_claim_allowed=allowed,
        reason_codes=tuple(sorted(set(reasons))) if reasons else ("target_benchmark_evidence_valid",),
        evidence_sha256=sha256_file(source),
    )


def build_development_benchmark_evidence(
    *,
    benchmark_id: str,
    benchmark_manifest_path: str | Path,
    host_report_path: str | Path,
    runtime_profile_sha256s: tuple[str, ...] = (),
) -> dict[str, Any]:
    manifest_sha = sha256_file(benchmark_manifest_path)
    host_sha = sha256_file(host_report_path)
    opportunity_sha = sha256_bytes(canonical_json_bytes({"benchmark_id": benchmark_id, "manifest": manifest_sha}))
    return {
        "schema": "sentinel-edge-target-benchmark-evidence/1.0",
        "benchmark_id": benchmark_id,
        "benchmark_manifest_sha256": manifest_sha,
        "host_report_sha256": host_sha,
        "runtime_profile_sha256s": list(runtime_profile_sha256s),
        "source_class": "simulated",
        "variants": [item.value for item in BenchmarkVariant],
        "quality_guardrails_passed": False,
        "thermal_valid": False,
        "power_valid": False,
        "target_host_qualified": False,
        "samples": [
            {
                "variant": item.value,
                "iteration": 0,
                "opportunity_manifest_sha256": opportunity_sha,
                "elapsed_ms": 0.0,
                "classification": "development_placeholder_not_measurement",
            }
            for item in BenchmarkVariant
        ],
    }
