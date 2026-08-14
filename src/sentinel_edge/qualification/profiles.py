from __future__ import annotations

import importlib.metadata
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sentinel_edge import __version__
from sentinel_edge.domain.models import (
    HostQualificationReport,
    CapabilityState,
    RuntimeProfileManifest,
    RuntimeProfileQualification,
)
from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file


def load_runtime_profile(path: str | Path) -> RuntimeProfileManifest:
    return RuntimeProfileManifest.model_validate_json(Path(path).read_text(encoding="utf-8"))


def _runtime_version(name: str) -> str | None:
    if name == "sentinel-edge":
        return __version__
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _verify_bindings(
    root: Path,
    bindings: tuple[Any, ...],
    *,
    required_assertion: str,
) -> tuple[bool, bool, list[str]]:
    reasons: list[str] = []
    target_assertions: list[bool] = []
    for binding in bindings:
        path = (root / binding.path).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError:
            reasons.append(f"evidence_path_outside_root:{binding.kind}")
            continue
        if not path.is_file():
            reasons.append(f"evidence_missing:{binding.kind}")
            continue
        if sha256_file(path) != binding.sha256:
            reasons.append(f"evidence_digest_mismatch:{binding.kind}")
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            reasons.append(f"evidence_not_json:{binding.kind}")
            continue
        if payload.get(required_assertion) is not True:
            reasons.append(f"evidence_assertion_failed:{binding.kind}:{required_assertion}")
        target_assertions.append(payload.get("target_qualified") is True)
    return not reasons, bool(target_assertions) and all(target_assertions), reasons


def qualify_runtime_profile(
    manifest: RuntimeProfileManifest,
    *,
    root: str | Path,
    host_report: HostQualificationReport | None = None,
    now: datetime | None = None,
) -> RuntimeProfileQualification:
    now = now or datetime.now(timezone.utc)
    root_path = Path(root).resolve()
    reasons: list[str] = []
    manifest_sha = sha256_bytes(canonical_json_bytes(manifest.model_dump(mode="json")))
    model_path = (root_path / manifest.model_path).resolve()
    try:
        model_path.relative_to(root_path)
    except ValueError:
        reasons.append("model_path_outside_root")
    model_match = model_path.is_file() and sha256_file(model_path) == manifest.model_sha256
    if not model_path.is_file():
        reasons.append("model_artifact_missing")
    elif not model_match:
        reasons.append("model_digest_mismatch")
    observed_runtime = _runtime_version(manifest.runtime_name)
    runtime_match = observed_runtime == manifest.runtime_version
    if observed_runtime is None:
        reasons.append("runtime_not_installed")
    elif not runtime_match:
        reasons.append("runtime_version_mismatch")
    quality_ok, quality_target, quality_reasons = _verify_bindings(
        root_path, manifest.quality_evidence, required_assertion="quality_guardrails_passed"
    )
    benchmark_ok, benchmark_target, benchmark_reasons = _verify_bindings(
        root_path, manifest.benchmark_evidence, required_assertion="profile_benchmark_passed"
    )
    if not manifest.quality_evidence:
        quality_ok = False
        quality_reasons.append("quality_evidence_missing")
    if not manifest.benchmark_evidence:
        benchmark_ok = False
        benchmark_reasons.append("benchmark_evidence_missing")
    reasons.extend(quality_reasons)
    reasons.extend(benchmark_reasons)
    host_match = manifest.host_report_sha256 is None
    if manifest.host_report_sha256 is not None:
        if host_report is None:
            reasons.append("host_report_missing")
            host_match = False
        else:
            host_digest = sha256_bytes(canonical_json_bytes(host_report.model_dump(mode="json")))
            host_match = host_digest == manifest.host_report_sha256 and host_report.host_profile_match
            if not host_match:
                reasons.append("host_report_binding_mismatch")
    if now >= manifest.expires_at:
        reasons.append("runtime_profile_expired")
    basic_valid = model_match and runtime_match and quality_ok and benchmark_ok and now < manifest.expires_at
    target_qualified = (
        basic_valid
        and host_match
        and host_report is not None
        and host_report.target_device_claim_allowed
        and quality_target
        and benchmark_target
    )
    state = CapabilityState.TARGET_QUALIFIED if target_qualified else (
        CapabilityState.TESTED if basic_valid else CapabilityState.FAILED
    )
    return RuntimeProfileQualification(
        profile_id=manifest.profile_id,
        manifest_sha256=manifest_sha,
        model_sha256=manifest.model_sha256,
        state=state,
        runtime_identity_match=runtime_match,
        model_integrity_match=model_match,
        host_binding_match=host_match,
        quality_evidence_complete=quality_ok,
        benchmark_evidence_complete=benchmark_ok,
        target_qualified=target_qualified,
        release_admissible=False,
        reason_codes=(
            tuple(sorted(set(reasons)))
            if reasons
            else (("runtime_profile_target_qualified",) if target_qualified else ("development_profile_evidence_complete_no_target_host_binding",))
        ),
    )


def write_json_report(path: str | Path, payload: Any) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(payload, "model_dump"):
        value = payload.model_dump(mode="json")
    else:
        value = payload
    output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output
