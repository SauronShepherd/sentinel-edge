from __future__ import annotations

import json
import os
import tempfile
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file
from sentinel_edge.release.provenance import verify_provenance
from sentinel_edge.release.advisories import verify_security_review
from sentinel_edge.release.reproducibility import verify_reproducibility_report
from sentinel_edge.release.wheelhouse import verify_target_wheelhouse_report, verify_wheelhouse_report
from sentinel_edge.qualification.network_isolation import verify_network_isolation_report
from sentinel_edge.qualification.host_security import verify_host_trust_report
from sentinel_edge.privacy import verify_privacy_closure
from sentinel_edge.benchmark import verify_analysis_report
from sentinel_edge.release.submission import RELEASE_GENERATED_FILES, verify_submission_command_matrix

_EXCLUDED = {".git", ".idea", ".tmp", ".venv", "build", "dist", "node_modules", ".agents", ".codex", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache"}
_EXCLUDED_FILES = set(RELEASE_GENERATED_FILES)
_ACTIVE_CONTRACT_GENERATOR_VERSION = "generate_active_contract_snapshot.py@1"


def _active_contract_binding(root: Path) -> dict[str, Any]:
    """Bind the current-contract inputs without treating cumulative prose as executable state."""
    inputs = [root / "registries/requirements.yaml", root / "registries/tasks.yaml", root / "registries/tests.yaml", root / "registries/iterations.yaml"]
    inputs.extend(sorted((root / "docs/contracts").glob("*v0.22.0.md")))
    records = [{"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)} for path in inputs if path.is_file()]
    return {
        "generator_version": _ACTIVE_CONTRACT_GENERATOR_VERSION,
        "inputs": records,
        "digest": sha256_bytes(canonical_json_bytes(records)),
    }


def _repository_state(root: Path) -> dict[str, Any]:
    try:
        raw_status = subprocess.run(["git", "status", "--porcelain=v1"], cwd=root, text=True, capture_output=True, check=True).stdout.splitlines()
        status: list[str] = []
        for entry in raw_status:
            # Generated release-candidate files are outputs of the admission
            # operation itself.  They must not make an otherwise clean source
            # revision invalidate the candidate immediately after generation.
            path_text = entry[3:] if len(entry) > 3 else entry
            if " -> " in path_text:
                path_text = path_text.split(" -> ", 1)[1]
            if path_text.replace("\\", "/") in _EXCLUDED_FILES:
                continue
            status.append(entry)
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()
        return {"git_available": True, "revision": revision, "dirty": bool(status), "status_entries": status}
    except (OSError, subprocess.SubprocessError):
        return {"git_available": False, "revision": None, "dirty": None, "status_entries": []}


def _inventory(root: Path) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in _EXCLUDED or part.endswith(".egg-info") for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix()
        if relative in _EXCLUDED_FILES or relative.endswith(".pyc"):
            continue
        files.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return files


def _requirements_summary(root: Path) -> dict[str, Any]:
    items = yaml.safe_load((root / "registries/requirements.yaml").read_text(encoding="utf-8"))["items"]
    by_status: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    for item in items:
        by_status[item["status"]] = by_status.get(item["status"], 0) + 1
        by_priority[item["priority"]] = by_priority.get(item["priority"], 0) + 1
    h0_open = [item["id"] for item in items if item["priority"] == "P0" and item["status"] not in {"IMPLEMENTED", "VERIFIED"}]
    return {
        "total": len(items),
        "by_status": dict(sorted(by_status.items())),
        "by_priority": dict(sorted(by_priority.items())),
        "h0_open_count": len(h0_open),
        "h0_open_sample": h0_open[:25],
    }


def _emulation_profile_summary(root: Path) -> dict[str, Any]:
    path = root / "config/arm64-emulation.yaml"
    if not path.is_file():
        return {"active": False, "valid": False, "failures": ["emulation_profile_missing"]}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {"active": False, "valid": False, "failures": ["emulation_profile_invalid_yaml"]}
    failures: list[str] = []
    execution = payload.get("execution", {}) if isinstance(payload.get("execution"), dict) else {}
    sensors = payload.get("sensors", {}) if isinstance(payload.get("sensors"), dict) else {}
    claims = payload.get("claims", {}) if isinstance(payload.get("claims"), dict) else {}
    if payload.get("profile_id") != "H0-EMULATED-AARCH64-20260813":
        failures.append("emulation_profile_id_mismatch")
    if execution.get("platform") != "linux/arm64" or execution.get("guest_architecture") != "aarch64":
        failures.append("emulation_guest_platform_mismatch")
    if execution.get("technology") != "docker-qemu":
        failures.append("emulation_technology_mismatch")
    if execution.get("image") != "python:3.13.15-slim":
        failures.append("emulation_python_image_not_pinned")
    image_digest = str(execution.get("image_digest", ""))
    if image_digest != "sha256:ffb752e139c0a19692a43af8d8523b274222dd68eebad5d583b45c2201c6e30a":
        failures.append("emulation_python_image_digest_not_pinned")
    dockerfile = root / "docker/Dockerfile.arm64"
    if not dockerfile.is_file() or f"python:3.13.15-slim@{image_digest}" not in dockerfile.read_text(encoding="utf-8"):
        failures.append("emulation_dockerfile_base_digest_mismatch")
    if str(execution.get("onnxruntime_version")) != "1.28.0":
        failures.append("emulation_onnxruntime_version_not_pinned")
    dependency_lock_rel = execution.get("dependency_lock")
    dependency_lock = root / str(dependency_lock_rel or "")
    artifact_manifest_rel = execution.get("runtime_artifact_manifest")
    artifact_manifest = root / str(artifact_manifest_rel or "")
    if dependency_lock_rel != "docker/requirements-arm64.lock.txt" or not dependency_lock.is_file():
        failures.append("emulation_dependency_lock_missing")
    else:
        lock_text = dependency_lock.read_text(encoding="utf-8")
        required_pins = (
            "flatbuffers==25.2.10",
            "numpy==2.3.5",
            "packaging==25.0",
            "protobuf==6.33.6",
            "onnxruntime==1.28.0",
        )
        missing_pins = [pin for pin in required_pins if pin not in lock_text]
        if missing_pins:
            failures.extend(f"emulation_dependency_pin_missing:{pin}" for pin in missing_pins)
        if "--hash=sha256:" not in lock_text:
            failures.append("emulation_dependency_hashes_missing")
    if artifact_manifest_rel != "config/arm64-python-artifacts.json" or not artifact_manifest.is_file():
        failures.append("emulation_runtime_artifact_manifest_missing")
    else:
        try:
            artifact_payload = json.loads(artifact_manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            artifact_payload = {}
            failures.append("emulation_runtime_artifact_manifest_invalid")
        if artifact_payload.get("schema") != "sentinel-edge.arm64-python-artifacts.v1":
            failures.append("emulation_runtime_artifact_manifest_schema_mismatch")
        for artifact in artifact_payload.get("artifacts", []):
            if not isinstance(artifact, dict):
                failures.append("emulation_runtime_artifact_entry_invalid")
                continue
            pin = f"{artifact.get('name')}=={artifact.get('version')}"
            digest = f"--hash=sha256:{artifact.get('sha256')}"
            if dependency_lock.is_file() and (pin not in lock_text or digest not in lock_text):
                failures.append(f"emulation_runtime_artifact_not_bound:{artifact.get('name')}")
    if sensors.get("physical_hardware_required") is not False:
        failures.append("emulation_profile_still_requires_physical_hardware")
    if sensors.get("mode") != "deterministic_simulated" or sensors.get("acquisition_contract") != "ObservationV2":
        failures.append("emulation_sensor_contract_mismatch")
    for key in ("raspberry_pi_performance_allowed", "physical_energy_allowed", "physical_thermal_allowed", "physical_sensor_quality_allowed"):
        if claims.get(key) is not False:
            failures.append(f"unsafe_emulation_claim_policy:{key}")
    return {
        "active": True,
        "valid": not failures,
        "profile_id": payload.get("profile_id"),
        "sha256": sha256_file(path),
        "dependency_lock_sha256": sha256_file(dependency_lock) if dependency_lock.is_file() else None,
        "runtime_artifact_manifest_sha256": sha256_file(artifact_manifest) if artifact_manifest.is_file() else None,
        "dockerfile_sha256": sha256_file(root / "docker/Dockerfile.arm64") if (root / "docker/Dockerfile.arm64").is_file() else None,
        "execution": execution,
        "sensors": sensors,
        "claims": claims,
        "failures": failures,
    }




def _emulated_benchmark_summary(root: Path) -> dict[str, Any]:
    path = root / "qualification/emulated-arm64-benchmark.json"
    if not path.is_file():
        return {"present": False, "valid": False, "failures": ["emulated_arm64_benchmark_missing"]}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"present": True, "valid": False, "failures": ["emulated_arm64_benchmark_invalid_json"]}
    failures: list[str] = []
    environment = payload.get("environment", {}) if isinstance(payload.get("environment"), dict) else {}
    runtime = environment.get("onnxruntime", {}) if isinstance(environment.get("onnxruntime"), dict) else {}
    providers = runtime.get("providers", []) if isinstance(runtime.get("providers"), list) else []
    if payload.get("schema") != "sentinel-edge.emulated-arm64-benchmark.v1":
        failures.append("emulated_arm64_benchmark_schema_mismatch")
    if payload.get("release_profile") != "H0-EMULATED-AARCH64-20260813":
        failures.append("emulated_arm64_benchmark_profile_mismatch")
    if str(environment.get("guest_architecture", "")).lower() not in {"aarch64", "arm64"}:
        failures.append("emulated_arm64_benchmark_guest_architecture_invalid")
    if environment.get("execution_mode") != "docker-qemu-linux-arm64":
        failures.append("emulated_arm64_benchmark_execution_mode_invalid")
    if "CPUExecutionProvider" not in providers:
        failures.append("emulated_arm64_benchmark_cpu_ep_missing")
    if str(runtime.get("version")) != "1.28.0":
        failures.append("emulated_arm64_benchmark_runtime_version_mismatch")
    known_answer = environment.get("known_answer_inference", {}) if isinstance(environment.get("known_answer_inference"), dict) else {}
    runtime_distribution = known_answer.get("runtime_distribution", {}) if isinstance(known_answer.get("runtime_distribution"), dict) else {}
    if known_answer.get("passed") is not True:
        failures.append("emulated_arm64_runtime_known_answer_failed")
    if known_answer.get("assigned_providers") != ["CPUExecutionProvider"]:
        failures.append("emulated_arm64_runtime_provider_assignment_invalid")
    if int(known_answer.get("model_bytes", 0) or 0) <= 0 or not known_answer.get("model_sha256"):
        failures.append("emulated_arm64_known_answer_model_identity_unbound")
    if not runtime_distribution.get("record_sha256") or not runtime_distribution.get("native_files"):
        failures.append("emulated_arm64_runtime_artifact_identity_unbound")
    container_image = environment.get("container_image", {}) if isinstance(environment.get("container_image"), dict) else {}
    if not container_image.get("id") or not container_image.get("ref"):
        failures.append("emulated_arm64_benchmark_container_image_unbound")
    if payload.get("claim_class") != "simulated":
        failures.append("emulated_arm64_benchmark_claim_class_unsafe")
    if payload.get("quality_guardrails_passed") is not True:
        failures.append("emulated_arm64_benchmark_quality_guardrails_failed")
    instrumentation = payload.get("instrumentation", {}) if isinstance(payload.get("instrumentation"), dict) else {}
    scheduler_overhead = instrumentation.get("scheduler_overhead", {}) if isinstance(instrumentation.get("scheduler_overhead"), dict) else {}
    if scheduler_overhead.get("measurement_class") != "measured_emulated_arm64" or int(scheduler_overhead.get("decision_count", 0) or 0) <= 0:
        failures.append("emulated_arm64_scheduler_overhead_missing")
    results = payload.get("results", {}) if isinstance(payload.get("results"), dict) else {}
    required_semantic_fields = {
        "total_service_ms",
        "total_queue_delay_ms",
        "heavy_model_invocation_count",
        "heavy_model_service_ms",
        "heavy_model_duty_cycle",
        "scheduler_decision_count",
    }
    for variant in ("B0", "B1", "O1"):
        row = results.get(variant, {}) if isinstance(results.get(variant), dict) else {}
        semantic = row.get("semantic", {}) if isinstance(row.get("semantic"), dict) else {}
        if not required_semantic_fields <= set(semantic):
            failures.append(f"emulated_arm64_semantic_metrics_missing:{variant}")
        samples = semantic.get("resource_samples", []) if isinstance(semantic.get("resource_samples"), list) else []
        if not samples or samples[0].get("evidence_class") != "simulated" or samples[0].get("physical_measurement") is not False:
            failures.append(f"emulated_arm64_resource_truth_label_invalid:{variant}")
    limitations = " ".join(str(item).lower() for item in payload.get("limitations", []))
    if "not raspberry pi 5 performance" not in limitations:
        failures.append("emulated_arm64_benchmark_pi_limitation_missing")
    return {
        "present": True,
        "valid": not failures,
        "sha256": sha256_file(path),
        "environment": environment,
        "quality_guardrails_passed": payload.get("quality_guardrails_passed", False),
        "claim_class": payload.get("claim_class"),
        "failures": failures,
    }


def _qualification_summary(root: Path) -> dict[str, Any]:
    directory = root / "qualification"
    paths = {
        "host": directory / "host-qualification.json",
        "imu_signal": directory / "sensor-commissioning.json",
        "camera_signal": directory / "camera-commissioning.json",
        "runtime_profile": directory / "runtime-profile-qualification.json",
        "model_quality": directory / "model-quality-report.json",
        "benchmark": directory / "benchmark-evidence-report.json",
        "source_readiness": directory / "source-readiness.json",
        "model_package": directory / "model-package-admission.json",
        "signal_chain": directory / "signal-chain-evaluation.json",
        "site_commissioning": directory / "site-commissioning.json",
        "platform_envelope": directory / "platform-runtime-envelope.json",
        "qualification_lifecycle": directory / "qualification-lifecycle.json",
        "runtime_known_answer": directory / "runtime-known-answer.json",
    }
    records: dict[str, Any] = {}
    failures: list[str] = []
    for kind, path in paths.items():
        if not path.is_file():
            records[kind] = {"present": False}
            if kind not in {"imu_signal", "camera_signal", "site_commissioning"}:
                failures.append(f"{kind}_qualification_missing")
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            records[kind] = {"present": True, "valid_json": False, "sha256": sha256_file(path)}
            failures.append(f"{kind}_qualification_invalid")
            continue
        records[kind] = {"present": True, "valid_json": True, "sha256": sha256_file(path), "payload": payload}
    host_ok = records.get("host", {}).get("payload", {}).get("target_device_claim_allowed") is True
    imu_ok = records.get("imu_signal", {}).get("payload", {}).get("physical_source_proven") is True and records.get("imu_signal", {}).get("payload", {}).get("state") == "field_qualified"
    camera_ok = records.get("camera_signal", {}).get("payload", {}).get("physical_source_proven") is True and records.get("camera_signal", {}).get("payload", {}).get("state") == "field_qualified"
    signal_ok = imu_ok or camera_ok
    runtime_ok = records.get("runtime_profile", {}).get("payload", {}).get("target_qualified") is True
    model_quality_ok = records.get("model_quality", {}).get("payload", {}).get("target_qualified") is True
    benchmark_ok = records.get("benchmark", {}).get("payload", {}).get("target_measurement_claim_allowed") is True
    source_ok = records.get("source_readiness", {}).get("payload", {}).get("h0_zero_live_source_valid") is True
    model_package_ok = records.get("model_package", {}).get("payload", {}).get("release_admissible") is True
    signal_chain_ok = records.get("signal_chain", {}).get("payload", {}).get("verified_claim_allowed") is True
    platform_envelope_ok = records.get("platform_envelope", {}).get("payload", {}).get("target_qualified") is True
    qualification_lifecycle_ok = records.get("qualification_lifecycle", {}).get("payload", {}).get("target_claim_allowed") is True
    runtime_known_answer_ok = records.get("runtime_known_answer", {}).get("payload", {}).get("target_qualified") is True
    target_ready = host_ok and signal_ok and runtime_ok and model_quality_ok and benchmark_ok and source_ok and model_package_ok and signal_chain_ok and platform_envelope_ok and qualification_lifecycle_ok and runtime_known_answer_ok
    if not host_ok:
        failures.append("target_host_not_qualified")
    if not signal_ok:
        failures.append("physical_signal_not_qualified")
    if not runtime_ok:
        failures.append("runtime_profile_not_target_qualified")
    if not model_quality_ok:
        failures.append("model_quality_not_target_qualified")
    if not benchmark_ok:
        failures.append("target_benchmark_not_valid")
    if not source_ok:
        failures.append("source_readiness_not_valid")
    if not model_package_ok:
        failures.append("release_model_package_not_admitted")
    if not signal_chain_ok:
        failures.append("signal_chain_not_target_qualified")
    if not platform_envelope_ok:
        failures.append("platform_runtime_envelope_not_target_qualified")
    if not qualification_lifecycle_ok:
        failures.append("qualification_evidence_window_not_target_qualified")
    if not runtime_known_answer_ok:
        failures.append("runtime_known_answer_not_target_qualified")
    return {
        "records": records,
        "physical_signal_paths": {"imu": imu_ok, "camera": camera_ok},
        "release_model_package_admitted": model_package_ok,
        "signal_chain_target_qualified": signal_chain_ok,
        "platform_runtime_envelope_target_qualified": platform_envelope_ok,
        "qualification_evidence_window_target_qualified": qualification_lifecycle_ok,
        "runtime_known_answer_target_qualified": runtime_known_answer_ok,
        "target_ready": target_ready,
        "failures": sorted(set(failures)),
    }

def _verify_digest_bound_report(path: Path, *, schema: str) -> dict[str, Any]:
    if not path.is_file():
        return {"valid": False, "release_eligible": False, "failures": ["report_missing"]}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"valid": False, "release_eligible": False, "failures": ["report_invalid_json"]}
    failures: list[str] = []
    if payload.get("schema") != schema:
        failures.append("report_schema_mismatch")
    claimed = payload.get("report_digest")
    base = {key: value for key, value in payload.items() if key != "report_digest"}
    if claimed != sha256_bytes(canonical_json_bytes(base)):
        failures.append("report_digest_mismatch")
    return {
        "valid": not failures,
        "release_eligible": payload.get("release_eligible", False) and not failures,
        "failures": failures,
        "payload": payload,
    }


def build_release_candidate(
    root: str | Path,
    *,
    version: str,
    configuration_state: dict[str, Any],
    capabilities: list[dict[str, Any]],
    claims: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    root_path = Path(root).resolve()
    inventory = _inventory(root_path)
    inventory_digest = sha256_bytes(canonical_json_bytes(inventory))
    requirements = _requirements_summary(root_path)
    sbom_path = root_path / "sbom.cdx.json"
    provenance_path = root_path / "build-provenance.json"
    security_review_path = root_path / "security-review.json"
    reproducibility_path = root_path / "reproducibility-report.json"
    host_trust_path = root_path / "host-trust-report.json"
    wheelhouse_path = root_path / "wheelhouse-report.json"
    network_isolation_path = root_path / "network-isolation-report.json"
    independent_build_path = root_path / "independent-build-report.json"
    release_governance_path = root_path / "release-governance-report.json"
    target_wheelhouse_path = root_path / "target-wheelhouse-report.json"
    benchmark_analysis_path = root_path / "benchmark-analysis-report.json"
    power_energy_path = root_path / "power-energy-report.json"
    runtime_known_issue_path = root_path / "runtime-known-issue-report.json"
    model_package_path = root_path / "qualification/model-package-admission.json"
    signal_chain_path = root_path / "qualification/signal-chain-evaluation.json"
    g0_gate_status_path = root_path / "qualification/g0-gate-status.json"
    claim_registry_path = root_path / "qualification/claim-registry.json"
    provenance_verification = verify_provenance(provenance_path, root_path) if provenance_path.is_file() else {"valid": False, "failures": ["missing_build_provenance"]}
    security_review_verification = (
        verify_security_review(security_review_path, sbom_path)
        if security_review_path.is_file() and sbom_path.is_file()
        else {"valid": False, "failures": ["missing_security_review_or_sbom"]}
    )
    security_review = json.loads(security_review_path.read_text(encoding="utf-8")) if security_review_path.is_file() else {}
    reproducibility_verification = verify_reproducibility_report(reproducibility_path, root_path) if reproducibility_path.is_file() else {"valid": False, "release_eligible": False, "failures": ["missing_reproducibility_report"]}
    host_trust_verification = verify_host_trust_report(host_trust_path) if host_trust_path.is_file() else {"valid": False, "release_eligible": False, "failures": ["missing_host_trust_report"]}
    wheelhouse_verification = verify_wheelhouse_report(wheelhouse_path) if wheelhouse_path.is_file() else {"valid": False, "release_eligible": False, "failures": ["missing_wheelhouse_report"]}
    network_isolation_verification = verify_network_isolation_report(network_isolation_path) if network_isolation_path.is_file() else {"valid": False, "release_eligible": False, "failures": ["missing_network_isolation_report"]}
    independent_build_verification = _verify_digest_bound_report(independent_build_path, schema="sentinel-edge-independent-build-report/1.0")
    release_governance_verification = _verify_digest_bound_report(release_governance_path, schema="sentinel-edge-release-governance-report/1.0")
    target_wheelhouse_verification = verify_target_wheelhouse_report(target_wheelhouse_path) if target_wheelhouse_path.is_file() else {"valid": False, "release_eligible": False, "target_platform_complete": False, "failures": ["missing_target_wheelhouse_report"]}
    benchmark_analysis_verification = verify_analysis_report(benchmark_analysis_path) if benchmark_analysis_path.is_file() else {"valid": False, "headline_eligible": False, "target_measurement_claim_allowed": False, "failures": ["missing_benchmark_analysis_report"]}
    power_energy_verification = _verify_digest_bound_report(power_energy_path, schema="sentinel-edge-power-energy-qualification/1.0")
    runtime_known_issue_verification = _verify_digest_bound_report(runtime_known_issue_path, schema="sentinel-edge-runtime-known-issue-evaluation/1.0")
    model_package_verification = _verify_digest_bound_report(model_package_path, schema="sentinel-edge-model-package-admission/1.0")
    signal_chain_verification = _verify_digest_bound_report(signal_chain_path, schema="sentinel-edge-signal-chain-evaluation/1.0")
    g0_gate_status = json.loads(g0_gate_status_path.read_text(encoding="utf-8")) if g0_gate_status_path.is_file() else {"packs": [], "release_admitted": False}
    claim_registry = json.loads(claim_registry_path.read_text(encoding="utf-8")) if claim_registry_path.is_file() else {}
    emulation_profile = _emulation_profile_summary(root_path)
    submission_matrix = verify_submission_command_matrix(root_path)
    emulated_benchmark = _emulated_benchmark_summary(root_path)
    claim_registry_valid = claim_registry.get("schema") == "sentinel-edge-claim-registry/1.0" and isinstance(claim_registry.get("claims"), list) and isinstance(claim_registry.get("source_artifacts"), list)
    if claim_registry_valid:
        source_digests: set[str] = set()
        for source in claim_registry["source_artifacts"]:
            source_path = root_path / str(source.get("path", ""))
            if not source_path.is_file() or sha256_file(source_path) != source.get("sha256"):
                claim_registry_valid = False
                break
            source_digests.add(str(source.get("sha256")))
        if claim_registry_valid:
            for claim in claim_registry["claims"]:
                if any(not isinstance(ref, str) or not ref.startswith("sha256:") or ref[7:] not in source_digests for ref in claim.get("artifact_refs", [])):
                    claim_registry_valid = False
                    break
    registry_claims = claim_registry.get("claims", []) if claim_registry_valid else []
    if claims is not None and claims != registry_claims:
        raise ValueError("candidate claims must match the validated Claim Registry")
    g0_packs = g0_gate_status.get("packs", [])
    g0_status_valid = (
        g0_gate_status.get("schema") == "sentinel-edge.g0-gate-status.v1"
        and [item.get("id") for item in g0_packs] == [f"G0-{index:02d}" for index in range(1, 13)]
        and all(item.get("status") in {"pass", "pass_with_declared_limitation", "fail", "not_applicable"} for item in g0_packs)
    )
    supply_chain = {
        "sbom_present": sbom_path.is_file(),
        "sbom_sha256": sha256_file(sbom_path) if sbom_path.is_file() else None,
        "sbom_scope": "declared_runtime_dependencies",
        "provenance_present": provenance_path.is_file(),
        "provenance_sha256": sha256_file(provenance_path) if provenance_path.is_file() else None,
        "provenance_verified": provenance_verification.get("valid", False),
        "provenance_failures": provenance_verification.get("failures", []),
        "security_review_present": security_review_path.is_file(),
        "security_review_sha256": sha256_file(security_review_path) if security_review_path.is_file() else None,
        "security_review_verified": security_review_verification.get("valid", False),
        "security_review_completeness": security_review.get("completeness", "missing"),
        "security_review_release_eligible": security_review.get("release_eligible", False),
        "security_review_blocking_count": len(security_review.get("blocking_findings", [])),
        "reproducibility_report_present": reproducibility_path.is_file(),
        "reproducibility_report_sha256": sha256_file(reproducibility_path) if reproducibility_path.is_file() else None,
        "reproducibility_verified": reproducibility_verification.get("valid", False),
        "reproducibility_release_eligible": reproducibility_verification.get("release_eligible", False),
        "reproducibility_failures": reproducibility_verification.get("failures", []),
        "host_trust_report_present": host_trust_path.is_file(),
        "host_trust_report_sha256": sha256_file(host_trust_path) if host_trust_path.is_file() else None,
        "host_trust_verified": host_trust_verification.get("valid", False),
        "host_trust_release_eligible": host_trust_verification.get("release_eligible", False),
        "host_trust_failures": host_trust_verification.get("failures", []),
        "wheelhouse_report_present": wheelhouse_path.is_file(),
        "wheelhouse_report_sha256": sha256_file(wheelhouse_path) if wheelhouse_path.is_file() else None,
        "wheelhouse_verified": wheelhouse_verification.get("valid", False),
        "wheelhouse_release_eligible": wheelhouse_verification.get("release_eligible", False),
        "wheelhouse_failures": wheelhouse_verification.get("failures", []),
        "network_isolation_report_present": network_isolation_path.is_file(),
        "network_isolation_report_sha256": sha256_file(network_isolation_path) if network_isolation_path.is_file() else None,
        "network_isolation_verified": network_isolation_verification.get("valid", False),
        "network_isolation_release_eligible": network_isolation_verification.get("release_eligible", False),
        "network_isolation_failures": network_isolation_verification.get("failures", []),
        "independent_build_report_present": independent_build_path.is_file(),
        "independent_build_report_sha256": sha256_file(independent_build_path) if independent_build_path.is_file() else None,
        "independent_build_verified": independent_build_verification.get("valid", False),
        "independent_build_release_eligible": independent_build_verification.get("release_eligible", False),
        "independent_build_failures": independent_build_verification.get("failures", []),
        "release_governance_report_present": release_governance_path.is_file(),
        "release_governance_report_sha256": sha256_file(release_governance_path) if release_governance_path.is_file() else None,
        "release_governance_verified": release_governance_verification.get("valid", False),
        "release_governance_release_eligible": release_governance_verification.get("release_eligible", False),
        "release_governance_failures": release_governance_verification.get("failures", []),
        "target_wheelhouse_report_present": target_wheelhouse_path.is_file(),
        "target_wheelhouse_report_sha256": sha256_file(target_wheelhouse_path) if target_wheelhouse_path.is_file() else None,
        "target_wheelhouse_verified": target_wheelhouse_verification.get("valid", False),
        "target_wheelhouse_release_eligible": target_wheelhouse_verification.get("release_eligible", False),
        "target_wheelhouse_failures": target_wheelhouse_verification.get("failures", []),
        "benchmark_analysis_report_present": benchmark_analysis_path.is_file(),
        "benchmark_analysis_report_sha256": sha256_file(benchmark_analysis_path) if benchmark_analysis_path.is_file() else None,
        "benchmark_analysis_verified": benchmark_analysis_verification.get("valid", False),
        "benchmark_analysis_headline_eligible": benchmark_analysis_verification.get("headline_eligible", False),
        "benchmark_analysis_target_measurement_allowed": benchmark_analysis_verification.get("target_measurement_claim_allowed", False),
        "benchmark_analysis_failures": benchmark_analysis_verification.get("failures", []),
        "power_energy_report_present": power_energy_path.is_file(),
        "power_energy_report_sha256": sha256_file(power_energy_path) if power_energy_path.is_file() else None,
        "power_energy_verified": power_energy_verification.get("valid", False),
        "power_energy_release_eligible": power_energy_verification.get("release_eligible", False),
        "power_energy_failures": power_energy_verification.get("failures", []),
        "runtime_known_issue_report_present": runtime_known_issue_path.is_file(),
        "runtime_known_issue_report_sha256": sha256_file(runtime_known_issue_path) if runtime_known_issue_path.is_file() else None,
        "runtime_known_issue_verified": runtime_known_issue_verification.get("valid", False),
        "runtime_known_issue_release_eligible": runtime_known_issue_verification.get("release_eligible", False),
        "runtime_known_issue_failures": runtime_known_issue_verification.get("failures", []),
        "model_package_report_present": model_package_path.is_file(),
        "model_package_report_sha256": sha256_file(model_package_path) if model_package_path.is_file() else None,
        "model_package_verified": model_package_verification.get("valid", False),
        "model_package_release_eligible": model_package_verification.get("payload", {}).get("release_admissible", False) and model_package_verification.get("valid", False),
        "model_package_failures": model_package_verification.get("failures", []),
        "signal_chain_report_present": signal_chain_path.is_file(),
        "signal_chain_report_sha256": sha256_file(signal_chain_path) if signal_chain_path.is_file() else None,
        "signal_chain_verified": signal_chain_verification.get("valid", False),
        "signal_chain_release_eligible": signal_chain_verification.get("payload", {}).get("verified_claim_allowed", False) and signal_chain_verification.get("valid", False),
        "signal_chain_failures": signal_chain_verification.get("failures", []),
        "signature_required_for_release": True,
    }
    qualification = _qualification_summary(root_path)
    privacy_path = root_path / "privacy-closure.json"
    privacy_verification = verify_privacy_closure(privacy_path) if privacy_path.is_file() else {
        "valid": False, "privacy_state_complete": False, "release_eligible": False,
        "failures": ["missing_privacy_closure"], "report_sha256": None,
    }
    privacy = {
        "present": privacy_path.is_file(),
        "sha256": sha256_file(privacy_path) if privacy_path.is_file() else None,
        "verified": privacy_verification.get("valid", False),
        "privacy_state_complete": privacy_verification.get("privacy_state_complete", False),
        "release_eligible": privacy_verification.get("release_eligible", False),
        "failures": privacy_verification.get("failures", []),
        "independent_review_complete": bool(release_governance_verification.get("payload", {}).get("independent_reviews_complete", False)) and release_governance_verification.get("valid", False),
    }
    active_config = configuration_state.get("active")
    active_config_digest = sha256_bytes(canonical_json_bytes(active_config)) if active_config else None
    candidate_bound_claims = all(
        claim.get("claim_class") in {"simulated", "research"} or bool(claim.get("release_candidate_id"))
        for claim in registry_claims
    )
    identity = {
        "schema": "sentinel-edge-release-candidate-identity/1.0",
        "project": "sentinel-edge",
        "version": version,
        "inventory_digest": inventory_digest,
        "active_configuration_digest": active_config_digest,
        "capabilities": capabilities,
        "claims": registry_claims,
        "requirements": requirements,
        "supply_chain": supply_chain,
        "security": {
            "authentication_profile": "bound_by_release_governance_report",
            "release_credentials_proven": bool(release_governance_verification.get("payload", {}).get("release_credentials_proven", False)) and release_governance_verification.get("valid", False),
            "independent_reviews_complete": bool(release_governance_verification.get("payload", {}).get("independent_reviews_complete", False)) and release_governance_verification.get("valid", False),
        },
        "qualification": qualification,
        "g0_gate_status": {
            "present": g0_gate_status_path.is_file(),
            "sha256": sha256_file(g0_gate_status_path) if g0_gate_status_path.is_file() else None,
            "valid": g0_status_valid,
            "release_admitted": bool(g0_gate_status.get("release_admitted", False)),
            "summary": g0_gate_status.get("summary", {}),
        },
        "claim_registry": {
            "present": claim_registry_path.is_file(),
            "sha256": sha256_file(claim_registry_path) if claim_registry_path.is_file() else None,
            "valid": claim_registry_valid,
            "claim_count": len(claim_registry.get("claims", [])),
        },
        "claim_artifact_scope": {"candidate_bound": candidate_bound_claims},
        "release_profile": emulation_profile.get("profile_id") if emulation_profile.get("valid") else g0_gate_status.get("release_profile"),
        "emulation_profile": emulation_profile,
        "emulated_arm64_benchmark": emulated_benchmark,
        "submission_command_matrix": {
            "present": submission_matrix.get("present", False),
            "valid": submission_matrix.get("valid", False),
            "sha256": submission_matrix.get("sha256"),
            "failures": submission_matrix.get("failures", []),
        },
        "privacy": privacy,
        "active_contract": _active_contract_binding(root_path),
        "repository_state": _repository_state(root_path),
        # Keep entrant-controlled bytes distinct from facts observed on the
        # qualification host; observed facts must never be promoted into the
        # frozen content inventory.
        "frozen_entrant_artifacts": {
            "repository_inventory_digest": inventory_digest,
            "active_configuration_digest": active_config_digest,
            "requirements_registry_sha256": sha256_file(root_path / "registries/requirements.yaml") if (root_path / "registries/requirements.yaml").is_file() else None,
        },
        "observed_environment": {
            "host_trust_report_sha256": supply_chain["host_trust_report_sha256"],
            "qualification_profile": qualification.get("profile"),
            "g0_gate_status_sha256": sha256_file(g0_gate_status_path) if g0_gate_status_path.is_file() else None,
        },
    }
    candidate_id = sha256_bytes(canonical_json_bytes(identity))
    common_release_ready = (
        requirements["h0_open_count"] == 0
        and all(item.get("state") == "healthy" for item in capabilities)
        and identity["repository_state"].get("git_available") is True
        and identity["repository_state"].get("dirty") is False
        and supply_chain["sbom_present"]
        and supply_chain["provenance_verified"]
        and supply_chain["security_review_verified"]
        and supply_chain["reproducibility_verified"]
        and supply_chain["host_trust_verified"]
        and supply_chain["wheelhouse_verified"]
        and supply_chain["network_isolation_verified"]
        and supply_chain["independent_build_verified"]
        and supply_chain["release_governance_verified"]
        and supply_chain["target_wheelhouse_verified"]
        and supply_chain["benchmark_analysis_verified"]
        and supply_chain["power_energy_verified"]
        and supply_chain["runtime_known_issue_verified"]
        and supply_chain["model_package_verified"]
        and supply_chain["signal_chain_verified"]
        and privacy["verified"]
        and privacy["release_eligible"]
        and identity["g0_gate_status"]["valid"]
        and identity["g0_gate_status"]["release_admitted"]
        and identity["claim_registry"]["valid"]
        and identity["claim_artifact_scope"]["candidate_bound"]
        and all(item.get("status") in {"pass", "pass_with_declared_limitation"} for item in g0_packs)
    )
    emulated_release = bool(
        common_release_ready
        and emulation_profile.get("valid")
        and submission_matrix.get("valid")
        and emulated_benchmark.get("valid")
        and qualification.get("records", {}).get("source_readiness", {}).get("payload", {}).get("h0_zero_live_source_valid") is True
        and all(claim.get("claim_class") in set(emulation_profile.get("claims", {}).get("allowed_classes", ())) for claim in registry_claims)
    )
    physical_target_release = bool(
        common_release_ready
        and not emulation_profile.get("active")
        and supply_chain["security_review_release_eligible"]
        and supply_chain["reproducibility_release_eligible"]
        and supply_chain["host_trust_release_eligible"]
        and supply_chain["wheelhouse_release_eligible"]
        and supply_chain["network_isolation_release_eligible"]
        and supply_chain["independent_build_release_eligible"]
        and supply_chain["release_governance_release_eligible"]
        and supply_chain["target_wheelhouse_release_eligible"]
        and supply_chain["benchmark_analysis_target_measurement_allowed"]
        and supply_chain["power_energy_release_eligible"]
        and supply_chain["runtime_known_issue_release_eligible"]
        and supply_chain["model_package_release_eligible"]
        and supply_chain["signal_chain_release_eligible"]
        and identity["security"]["release_credentials_proven"]
        and identity["security"]["independent_reviews_complete"]
        and qualification["target_ready"]
    )
    release_admitted = emulated_release or physical_target_release
    admission_blockers: list[str] = []
    if requirements["h0_open_count"]:
        admission_blockers.append(f"h0_open:{requirements['h0_open_count']}")
    if identity["repository_state"].get("git_available") is not True:
        admission_blockers.append("git_revision_unavailable")
    elif identity["repository_state"].get("dirty") is not False:
        admission_blockers.append("repository_dirty")
    if not emulation_profile.get("valid") and emulation_profile.get("active"):
        admission_blockers.extend(emulation_profile.get("failures", []))
    if emulation_profile.get("active") and not submission_matrix.get("valid"):
        admission_blockers.extend(submission_matrix.get("failures", []))
    if emulation_profile.get("active") and not emulated_benchmark.get("valid"):
        admission_blockers.extend(emulated_benchmark.get("failures", []))
    if not supply_chain["provenance_verified"]:
        admission_blockers.append("provenance_not_verified")
    if not supply_chain["security_review_verified"]:
        admission_blockers.append("security_review_not_verified")
    if not supply_chain["reproducibility_verified"]:
        admission_blockers.append("reproducibility_not_verified")
    if not privacy["verified"] or not privacy["release_eligible"]:
        admission_blockers.append("privacy_closure_not_release_eligible")
    if not identity["claim_registry"]["valid"]:
        admission_blockers.append("claim_registry_invalid")
    if not identity["g0_gate_status"]["valid"] or not identity["g0_gate_status"]["release_admitted"]:
        admission_blockers.append("g0_gate_status_not_admitted")
    admission_blockers = sorted(set(admission_blockers))
    return {
        "schema": "sentinel-edge-release-candidate/1.0",
        "candidate_id": candidate_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "identity": identity,
        "inventory": inventory,
        "configuration": configuration_state,
        "release_profile": identity.get("release_profile"),
        "release_admitted": release_admitted,
        "admission_blockers": admission_blockers,
        "admission_reason": (
            "emulated_h0_candidate_closed" if emulated_release else
            "physical_target_candidate_closed" if physical_target_release else
            "development_candidate_only"
        ),
    }


def write_release_candidate(
    root: str | Path,
    *,
    version: str,
    configuration_state: dict[str, Any],
    capabilities: list[dict[str, Any]],
    claims: list[dict[str, Any]] | None = None,
    output: str | Path | None = None,
) -> Path:
    root_path = Path(root).resolve()
    output_path = Path(output) if output else root_path / "release-candidate.json"
    payload = build_release_candidate(
        root_path,
        version=version,
        configuration_state=configuration_state,
        capabilities=capabilities,
        claims=claims,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".tmp-release-candidate-", dir=output_path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, output_path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return output_path


def verify_release_candidate(path: str | Path, root: str | Path) -> dict[str, Any]:
    candidate_path = Path(path)
    root_path = Path(root).resolve()
    payload = json.loads(candidate_path.read_text(encoding="utf-8"))
    identity = payload["identity"]
    expected_id = sha256_bytes(canonical_json_bytes(identity))
    failures: list[str] = []
    if expected_id != payload.get("candidate_id"):
        failures.append("candidate_identity_mismatch")
    if identity.get("active_contract") != _active_contract_binding(root_path):
        failures.append("active_contract_binding_mismatch")
    if identity.get("repository_state") != _repository_state(root_path):
        failures.append("repository_state_mismatch")
    current_submission = verify_submission_command_matrix(root_path)
    bound_submission = identity.get("submission_command_matrix", {})
    if (
        bound_submission.get("present") != current_submission.get("present")
        or bound_submission.get("valid") != current_submission.get("valid")
        or bound_submission.get("sha256") != current_submission.get("sha256")
        or bound_submission.get("failures", []) != current_submission.get("failures", [])
    ):
        failures.append("submission_command_matrix_binding_mismatch")
    current_emulated_benchmark = _emulated_benchmark_summary(root_path)
    if identity.get("emulated_arm64_benchmark") != current_emulated_benchmark:
        failures.append("emulated_arm64_benchmark_binding_mismatch")
    if payload.get("release_admitted") and identity.get("repository_state", {}).get("dirty"):
        failures.append("dirty_repository_not_admissible")
    g0_path = root_path / "qualification/g0-gate-status.json"
    if not g0_path.is_file():
        failures.append("g0_gate_status_missing")
    else:
        try:
            g0 = json.loads(g0_path.read_text(encoding="utf-8"))
            packs = g0.get("packs", [])
            g0_valid = (
                g0.get("schema") == "sentinel-edge.g0-gate-status.v1"
                and [item.get("id") for item in packs] == [f"G0-{index:02d}" for index in range(1, 13)]
                and all(item.get("status") in {"pass", "pass_with_declared_limitation", "fail", "not_applicable"} for item in packs)
            )
            bound = identity.get("g0_gate_status", {})
            if not g0_valid or bound.get("sha256") != sha256_file(g0_path) or bound.get("summary") != g0.get("summary"):
                failures.append("g0_gate_status_binding_mismatch")
        except (OSError, json.JSONDecodeError, TypeError):
            failures.append("g0_gate_status_invalid")
    claim_path = root_path / "qualification/claim-registry.json"
    claim_binding = identity.get("claim_registry", {})
    if not claim_path.is_file() or claim_binding.get("sha256") != sha256_file(claim_path):
        failures.append("claim_registry_binding_mismatch")
    if claim_binding.get("valid") is not True:
        failures.append("claim_registry_invalid")
    current_inventory = _inventory(root_path)
    current_digest = sha256_bytes(canonical_json_bytes(current_inventory))
    if current_digest != identity.get("inventory_digest"):
        failures.append("inventory_digest_mismatch")
    expected_by_path = {item["path"]: item for item in payload.get("inventory", [])}
    current_by_path = {item["path"]: item for item in current_inventory}
    missing = sorted(set(expected_by_path) - set(current_by_path))
    extra = sorted(set(current_by_path) - set(expected_by_path))
    changed = sorted(
        path for path in set(expected_by_path) & set(current_by_path)
        if expected_by_path[path] != current_by_path[path]
    )
    if missing:
        failures.append("inventory_missing_paths")
    if extra:
        failures.append("inventory_extra_paths")
    if changed:
        failures.append("inventory_changed_paths")
    if expected_by_path != current_by_path:
        failures.append("inventory_contents_changed")
    return {
        "valid": not failures,
        "candidate_id": payload.get("candidate_id"),
        "failures": failures,
        "inventory_diff": {"missing": missing, "extra": extra, "changed": changed},
    }
