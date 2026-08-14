from __future__ import annotations

import argparse
import json
import platform
import shutil
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization

from sentinel_edge import __version__
from sentinel_edge.benchmark import (
    BenchmarkAnalysisPlan,
    BenchmarkExecutionRecord,
    DeterministicBenchmarkLab,
    FileIdentitySpec,
    SignedBenchmarkPlan,
    analyze_execution,
    load_benchmark_manifest,
    sign_analysis_plan,
    verify_file_identities,
    verify_signed_plan,
)
from sentinel_edge.configuration import load_configuration_bundle
from sentinel_edge.domain.models import BenchmarkVariant, HostQualificationReport, RuntimeMode, TimeSourceObservation
from sentinel_edge.gateway import create_app
from sentinel_edge.qualification import (
    build_development_benchmark_evidence,
    commission_camera,
    commission_imu,
    load_host_profile,
    load_model_quality_manifest,
    load_runtime_profile,
    load_source_observation,
    load_source_policy,
    observe_host,
    qualify_host,
    qualify_model_quality,
    qualify_runtime_profile,
    qualify_source,
    summarize_sources,
    validate_benchmark_evidence,
    write_json_report,
    write_host_trust_report,
    verify_host_trust_report,
    observe_benchmark_host,
    evaluate_idle_noise,
    evaluate_network_isolation,
    write_network_isolation_report,
    verify_network_isolation_report,
    SignalChainObservation,
    SignedSignalChainProfile,
    SignedSiteCommissioningRecord,
    evaluate_signal_chain,
    evaluate_site_commissioning,
    QualificationEvidenceWindow,
    QualificationClaim,
    evaluate_evidence_window,
    enforce_claim_ceiling,
    PlatformRuntimeEnvelope,
    evaluate_platform_runtime_envelope,
)
from sentinel_edge.audit import AuditCheckpoint
from sentinel_edge.security import AuthManager, KeyPurpose, generate_bearer_token
from sentinel_edge.review import AfterEventReviewBuilder
from sentinel_edge.release import (
    ClaimRegistry,
    verify_release_candidate,
    write_manifest,
    write_release_candidate,
    write_cyclonedx_sbom,
    write_third_party_inventory,
    write_third_party_notices,
    sign_release_candidate,
    verify_release_signature,
    write_provenance,
    verify_provenance,
    write_security_review,
    verify_security_review,
    write_reproducibility_report,
    verify_reproducibility_report,
    write_release_lock,
    scan_toolchain_inventory,
    mirror_installed_resolution,
    verify_wheelhouse,
    verify_target_wheelhouse,
)
from sentinel_edge.update import (
    OfflineUpdateManager,
    build_update_bundle,
    generate_keypair,
    load_private_key,
    load_public_key,
)
from sentinel_edge.scenario import DeterministicScenarioEngine, load_scenario, load_signed_scenario, run_submission_scenario_proof
from sentinel_edge.runtime import (
    TrustedTimeManager,
    ModelPackageManifest,
    RuntimeAdmissionContext,
    admit_model_package,
    inspect_onnx_graph,
    scan_model_execution_boundaries,
)
from sentinel_edge.geospatial import validate_geojson_geometry
from sentinel_edge.evolution import LegacyObservationPolicy, ObservationMigrator
from sentinel_edge.storage import StateBackupManager
from sentinel_edge.media import BoundedMediaParser
from sentinel_edge.exports import DerivedArtifactSelection, EvidenceExportSelection
from sentinel_edge.privacy import verify_privacy_closure, write_privacy_closure, write_tombstone_journal


def doctor() -> int:
    host_observation = observe_host()
    profile_path = Path("fixtures/qualification/raspberry-pi-5-h0.json")
    host_qualification = qualify_host(load_host_profile(profile_path), host_observation) if profile_path.is_file() else None
    report = {
        "sentinel_edge_version": __version__,
        "python": sys.version.split()[0],
        "machine": platform.machine(),
        "system": platform.system(),
        "architecture_64bit": sys.maxsize > 2**32,
        "arm64_target_observed": platform.machine().lower() in {"aarch64", "arm64"},
        "native_arm64_linux_observed": (
            platform.system().lower() == "linux"
            and sys.maxsize > 2**32
            and platform.machine().lower() in {"aarch64", "arm64"}
        ),
        "physical_signal_evidence_available": False,
        "hackathon_release_profile": "H0-EMULATED-AARCH64-20260813",
        "emulated_arm64_profile_available": Path("config/arm64-emulation.yaml").exists(),
        "physical_sensors_required_for_hackathon_profile": False,
        "sensor_input_mode": "deterministic_simulated_or_fixture",
        "raspberry_pi_performance_claim_allowed": False,
        "host_observation": host_observation.model_dump(mode="json"),
        "host_qualification": host_qualification.model_dump(mode="json") if host_qualification else None,
        "offline_fixture_ready": Path("fixtures/scenarios/simultaneous-event.signed.json").exists() and Path("fixtures/scenarios/simultaneous-event.public.pem").exists(),
        "benchmark_fixture_ready": Path("fixtures/scenarios/benchmark-open-loop.json").exists(),
        "configuration_fixture_ready": Path("fixtures/configuration/default-v0.21.0.yaml").exists(),
        "transactional_notification_outbox": True,
        "authenticated_rest_boundary": True,
        "principal_scoped_idempotency": True,
        "offline_update_signature_verification": True,
        "pwa_cache_default_deny": True,
        "authenticated_projection_stream": True,
        "offline_command_reauthorization": True,
        "build_provenance_available": Path("build-provenance.json").exists(),
        "security_review_available": Path("security-review.json").exists(),
        "host_qualification_profile_ready": Path("fixtures/qualification/raspberry-pi-5-h0.json").exists(),
        "camera_commissioning_fixture_ready": Path("fixtures/camera/wildfire-camera-5fps-development.jsonl").exists(),
        "model_quality_fixture_ready": Path("fixtures/models/wildfire-smoke-quality.manifest.json").exists(),
        "source_policy_fixture_ready": Path("fixtures/sources/meteoalarm-fixture.policy.json").exists(),
        "measurement_contract_v2": True,
        "trusted_time_policy": True,
        "rfc7946_geospatial_validation": True,
        "authority_subtype_conformance": True,
        "signed_audit_checkpoint_support": True,
        "audit_checkpoint_non_forensic": True,
        "protected_state_revocation_purge": True,
        "connector_bounded_shutdown": True,
        "schema_migration_rehearsal": True,
        "evidence_lifecycle_journal": True,
        "rights_expiry_enforcement": True,
        "bounded_media_parser": True,
        "media_parser_release_eligible": False,
        "qualification_state": "development_host_only",
        "warning": "Research monitoring and decision support; not an official warning authority.",
    }
    # Keep physical-reference qualification truth visible without allowing it to
    # masquerade as an H0 blocker.  The active hackathon profile explicitly
    # admits deterministic simulated physical-AI inputs in an emulated AArch64
    # Linux guest.  Physical Raspberry Pi/sensor evidence is relevant only to
    # stronger physical-target performance/field claims.
    report["reference_physical_target_blockers"] = [
        *( [] if report["native_arm64_linux_observed"] else ["native_arm64_linux_observation_missing"] ),
        "physical_signal_capture_evidence_missing",
    ]
    report["hackathon_profile_blockers"] = (
        []
        if report["emulated_arm64_profile_available"] and report["offline_fixture_ready"]
        else ["emulated_profile_or_signed_fixture_missing"]
    )
    # Backward-compatible field: this now reports blockers for the selected
    # release target, not the optional Raspberry Pi physical-reference target.
    report["target_qualification_blockers"] = list(report["hackathon_profile_blockers"])
    report["hackathon_profile_ready"] = not report["hackathon_profile_blockers"]
    report["reference_physical_target_qualified"] = not report["reference_physical_target_blockers"]
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["architecture_64bit"] and report["offline_fixture_ready"] else 1


def run_scenario(path: str, state_dir: str | None = None, public_key: str | None = None) -> int:
    # A signed fixture replay is a resettable run.  Clear only the explicitly
    # supplied scenario state directory so a prior replay cannot contaminate
    # sequence, watermark, or authority-journal state.
    if state_dir:
        target = Path(state_dir)
        if target.exists():
            shutil.rmtree(target)
    if public_key:
        scenario, manifest_sha256 = load_signed_scenario(path, load_public_key(public_key))
    else:
        scenario, manifest_sha256 = load_scenario(path), None
    if scenario.get("scenario_id") == "simultaneous-event-v1":
        proof = run_submission_scenario_proof(
            scenario, manifest_sha256=manifest_sha256, output_dir=".tmp/scenario-proof"
        )
        print(json.dumps(proof, indent=2, sort_keys=True))
        return 0 if proof.get("all_invariants_passed") is True else 2
    result = DeterministicScenarioEngine(state_dir=state_dir).run(scenario, manifest_sha256=manifest_sha256)
    print(result.model_dump_json(indent=2))
    return 0


def benchmark(path: str, iterations: int) -> int:
    scenario = load_scenario(path)
    samples = []
    result = None
    for _ in range(iterations):
        start = time.perf_counter_ns()
        result = DeterministicScenarioEngine().run(scenario)
        samples.append((time.perf_counter_ns() - start) / 1_000_000)
    output = {
        "iterations": iterations,
        "median_ms": statistics.median(samples),
        "min_ms": min(samples),
        "max_ms": max(samples),
        "determinism_class": "semantic",
        "final_states": result.final_states if result else {},
        "claim_class": "development_measurement",
        "target_qualification": False,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def benchmark_replay(path: str) -> int:
    manifest = load_benchmark_manifest(path)
    lab = DeterministicBenchmarkLab()
    output = {
        "schema": "sentinel-edge-benchmark-replay/1.0",
        "scenario_id": manifest["scenario_id"],
        "claim_class": "simulated",
        "runs": [lab.run(manifest, variant).model_dump(mode="json") for variant in BenchmarkVariant],
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


def activate_configuration(path: str, state_dir: str, fail_canary: bool) -> int:
    engine = DeterministicScenarioEngine(state_dir=state_dir)
    record = engine.activate_configuration(load_configuration_bundle(path), fail_canary=fail_canary)
    print(json.dumps({"activation": record.model_dump(mode="json"), "state": engine.configuration.state()}, indent=2, sort_keys=True))
    return 0 if record.state.value == "active" else 2


def build_candidate(root: str, state_dir: str, output: str | None) -> int:
    engine = DeterministicScenarioEngine(state_dir=state_dir)
    root_path = Path(root)
    claim_path = root_path / "qualification/claim-registry.json"
    claims = [item.model_dump(mode="json") for item in ClaimRegistry.read(claim_path).records()] if claim_path.is_file() else []
    path = write_release_candidate(
        root,
        version=__version__,
        configuration_state=engine.configuration.state(),
        capabilities=[item.model_dump(mode="json") for item in engine.capabilities.records()],
        claims=claims,
        output=output,
    )
    print(path)
    return 0


def verify_candidate(path: str, root: str) -> int:
    result = verify_release_candidate(path, root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1



def after_event_review(path: str, state_dir: str, output: str | None) -> int:
    engine = DeterministicScenarioEngine(state_dir=state_dir)
    result = engine.run(load_scenario(path))
    builder = AfterEventReviewBuilder()
    review = builder.build(engine, result)
    ref = builder.write(engine, result, engine.configuration.artifacts)
    payload = {"artifact": ref.__dict__, "review": review, "verified": builder.verify(review)}
    if output:
        Path(output).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0

def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("datetime must include an explicit timezone")
    return parsed.astimezone(timezone.utc)


def _update_self_test(root: Path) -> bool:
    required = root / "src" / "sentinel_edge" / "__init__.py"
    if not required.is_file():
        return False
    try:
        compile(required.read_text(encoding="utf-8"), str(required), "exec")
    except SyntaxError:
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(prog="sentinel-edge")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    run = sub.add_parser("run-scenario")
    run.add_argument("path")
    run.add_argument("--state-dir")
    run.add_argument("--public-key", help="verify a signed scenario envelope before execution")
    bench = sub.add_parser("benchmark")
    bench.add_argument("path")
    bench.add_argument("--iterations", type=int, default=5)
    replay = sub.add_parser("benchmark-replay")
    replay.add_argument("path")
    replay.add_argument("--state-dir")
    aer = sub.add_parser("after-event-review")
    aer.add_argument("path")
    aer.add_argument("--state-dir", required=True)
    aer.add_argument("--output")
    config = sub.add_parser("activate-configuration")
    config.add_argument("path")
    config.add_argument("--state-dir", required=True)
    config.add_argument("--fail-canary", action="store_true")
    serve = sub.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--auth-mode", choices=["development", "environment"], default="development")
    manifest = sub.add_parser("build-manifest")
    manifest.add_argument("--root", default=".")
    candidate = sub.add_parser("build-release-candidate")
    candidate.add_argument("--root", default=".")
    candidate.add_argument("--state-dir", required=True)
    candidate.add_argument("--output")
    verify = sub.add_parser("verify-release-candidate")
    verify.add_argument("path")
    verify.add_argument("--root", default=".")
    sbom = sub.add_parser("build-sbom")
    sbom.add_argument("--root", default=".")
    sbom.add_argument("--output")
    inventory = sub.add_parser("build-third-party-inventory")
    inventory.add_argument("--root", default=".")
    inventory.add_argument("--output")
    notices = sub.add_parser("build-third-party-notices")
    notices.add_argument("--root", default=".")
    notices.add_argument("--output")
    provenance = sub.add_parser("build-provenance")
    provenance.add_argument("--root", default=".")
    provenance.add_argument("--output")
    verify_prov = sub.add_parser("verify-provenance")
    verify_prov.add_argument("path")
    verify_prov.add_argument("--root", default=".")
    verify_prov.add_argument("--expected-builder")
    security_review = sub.add_parser("build-security-review")
    security_review.add_argument("--root", default=".")
    security_review.add_argument("--snapshot", action="append", required=True)
    security_review.add_argument("--output")
    verify_security = sub.add_parser("verify-security-review")
    verify_security.add_argument("path")
    verify_security.add_argument("--sbom", default="sbom.cdx.json")
    lock = sub.add_parser("build-release-lock")
    lock.add_argument("--root", default=".")
    lock.add_argument("--output")
    mirror = sub.add_parser("build-offline-wheelhouse")
    mirror.add_argument("--lock", default="requirements-release.lock.json")
    mirror.add_argument("--output-dir", default="artifacts/wheelhouse")
    mirror.add_argument("--report", default="wheelhouse-report.json")
    verify_mirror = sub.add_parser("verify-offline-wheelhouse")
    verify_mirror.add_argument("--lock", default="requirements-release.lock.json")
    verify_mirror.add_argument("--wheelhouse", default="artifacts/wheelhouse")
    verify_mirror.add_argument("--report")
    target_mirror = sub.add_parser("verify-target-wheelhouse")
    target_mirror.add_argument("--lock", default="requirements-release.lock.json")
    target_mirror.add_argument("--manifest", required=True)
    target_mirror.add_argument("--root", default=".")
    target_mirror.add_argument("--target-tag", action="append", required=True)
    target_mirror.add_argument("--report")
    plan_sign = sub.add_parser("sign-benchmark-plan")
    plan_sign.add_argument("plan")
    plan_sign.add_argument("--private-key", required=True)
    plan_sign.add_argument("--output", required=True)
    plan_verify = sub.add_parser("verify-benchmark-plan")
    plan_verify.add_argument("plan")
    plan_verify.add_argument("--public-key", required=True)
    identity_verify = sub.add_parser("verify-benchmark-identities")
    identity_verify.add_argument("spec")
    identity_verify.add_argument("--root", default=".")
    identity_verify.add_argument("--output")
    analysis = sub.add_parser("analyze-benchmark-execution")
    analysis.add_argument("signed_plan")
    analysis.add_argument("execution")
    analysis.add_argument("--public-key", required=True)
    analysis.add_argument("--network-report", required=True)
    analysis.add_argument("--host-report", required=True)
    analysis.add_argument("--runtime-report", action="append", required=True)
    analysis.add_argument("--wheelhouse-report", required=True)
    analysis.add_argument("--output", required=True)
    network_probe = sub.add_parser("probe-network-isolation")
    network_probe.add_argument("--output", default="network-isolation-report.json")
    network_verify = sub.add_parser("verify-network-isolation")
    network_verify.add_argument("path")
    repro = sub.add_parser("build-reproducibility-report")
    repro.add_argument("--root", default=".")
    repro.add_argument("--output")
    verify_repro = sub.add_parser("verify-reproducibility-report")
    verify_repro.add_argument("path")
    verify_repro.add_argument("--root", default=".")
    host_trust = sub.add_parser("observe-host-trust")
    host_trust.add_argument("--output", default="host-trust-report.json")
    host_trust.add_argument("--require-secure-boot", action="store_true")
    verify_host_trust = sub.add_parser("verify-host-trust")
    verify_host_trust.add_argument("path")
    toolchain = sub.add_parser("scan-toolchain")
    toolchain.add_argument("path", nargs="*")
    token = sub.add_parser("generate-bearer-token")
    keygen = sub.add_parser("generate-signing-key")
    keygen.add_argument("--private", required=True)
    keygen.add_argument("--public", required=True)
    sign = sub.add_parser("sign-release-candidate")
    sign.add_argument("candidate")
    sign.add_argument("--private-key", required=True)
    sign.add_argument("--output")
    verify_sig = sub.add_parser("verify-release-signature")
    verify_sig.add_argument("candidate")
    verify_sig.add_argument("signature")
    verify_sig.add_argument("--public-key", required=True)
    update_build = sub.add_parser("build-update-bundle")
    update_build.add_argument("--root", default=".")
    update_build.add_argument("--target", action="append", required=True)
    update_build.add_argument("--private-key", required=True)
    update_build.add_argument("--bundle-id", required=True)
    update_build.add_argument("--update-version", type=int, required=True)
    update_build.add_argument("--created-at", required=True)
    update_build.add_argument("--expires-at", required=True)
    update_build.add_argument("--compatible-min-version", required=True)
    update_build.add_argument("--compatible-max-version", required=True)
    update_build.add_argument("--output", required=True)
    update_verify = sub.add_parser("verify-update-bundle")
    update_verify.add_argument("bundle")
    update_verify.add_argument("--public-key", required=True)
    update_verify.add_argument("--state-dir", required=True)
    update_verify.add_argument("--mode", choices=[item.value for item in RuntimeMode], default=RuntimeMode.FIELD_LAB.value)
    update_verify.add_argument("--now")
    update_stage = sub.add_parser("stage-update-bundle")
    update_stage.add_argument("bundle")
    update_stage.add_argument("--public-key", required=True)
    update_stage.add_argument("--state-dir", required=True)
    update_stage.add_argument("--mode", choices=[item.value for item in RuntimeMode], default=RuntimeMode.FIELD_LAB.value)
    update_stage.add_argument("--now")
    update_activate = sub.add_parser("activate-staged-update")
    update_activate.add_argument("staged_path")
    update_activate.add_argument("--public-key", required=True)
    update_activate.add_argument("--state-dir", required=True)
    update_activate.add_argument("--now")
    host_observe = sub.add_parser("observe-host")
    host_observe.add_argument("--output")
    host_qualify = sub.add_parser("qualify-host")
    host_qualify.add_argument("profile")
    host_qualify.add_argument("--output")
    imu = sub.add_parser("commission-imu")
    imu.add_argument("path")
    imu.add_argument("--source-id", required=True)
    imu.add_argument("--rate-hz", type=float, required=True)
    imu.add_argument("--minimum-samples", type=int, default=100)
    imu.add_argument("--output")
    camera = sub.add_parser("commission-camera")
    camera.add_argument("path")
    camera.add_argument("--source-id", required=True)
    camera.add_argument("--fps", type=float, required=True)
    camera.add_argument("--minimum-frames", type=int, default=60)
    camera.add_argument("--output")
    model_quality = sub.add_parser("qualify-model-quality")
    model_quality.add_argument("manifest")
    model_quality.add_argument("--root", default=".")
    model_quality.add_argument("--now")
    model_quality.add_argument("--output")
    source_quality = sub.add_parser("qualify-source")
    source_quality.add_argument("policy")
    source_quality.add_argument("observation")
    source_quality.add_argument("--now")
    source_quality.add_argument("--output")
    source_summary = sub.add_parser("summarize-sources")
    source_summary.add_argument("report", nargs="*")
    source_summary.add_argument("--output", required=True)
    runtime_profile = sub.add_parser("qualify-runtime-profile")
    runtime_profile.add_argument("manifest")
    runtime_profile.add_argument("--root", default=".")
    runtime_profile.add_argument("--host-report")
    runtime_profile.add_argument("--output")
    inspect_model = sub.add_parser("inspect-onnx-model")
    inspect_model.add_argument("path")
    inspect_model.add_argument("--output")
    admit_model = sub.add_parser("admit-model-package")
    admit_model.add_argument("manifest")
    admit_model.add_argument("--runtime-context", required=True)
    admit_model.add_argument("--runtime-issues", required=True)
    admit_model.add_argument("--root", default=".")
    admit_model.add_argument("--now")
    admit_model.add_argument("--output")
    boundary_scan = sub.add_parser("scan-model-execution-boundary")
    boundary_scan.add_argument("--root", default=".")
    boundary_scan.add_argument("--output")
    signal_eval = sub.add_parser("evaluate-signal-chain")
    signal_eval.add_argument("profile")
    signal_eval.add_argument("observation")
    signal_eval.add_argument("--public-key", required=True)
    signal_eval.add_argument("--model-profile-id", required=True)
    signal_eval.add_argument("--now")
    signal_eval.add_argument("--output")
    commissioning_eval = sub.add_parser("evaluate-site-commissioning")
    commissioning_eval.add_argument("record")
    commissioning_eval.add_argument("--public-key", required=True)
    commissioning_eval.add_argument("--signal-chain-report", required=True)
    commissioning_eval.add_argument("--sensor-identity", required=True)
    commissioning_eval.add_argument("--configuration-sha256", required=True)
    commissioning_eval.add_argument("--mounting-or-pose", required=True)
    commissioning_eval.add_argument("--model-profile-id", required=True)
    commissioning_eval.add_argument("--now")
    commissioning_eval.add_argument("--output")
    qualification_window = sub.add_parser("evaluate-qualification-window")
    qualification_window.add_argument("window")
    qualification_window.add_argument("--now")
    qualification_window.add_argument("--output")
    qualification_claim = sub.add_parser("evaluate-qualification-claim")
    qualification_claim.add_argument("claim")
    qualification_claim.add_argument("evaluation", nargs="+")
    qualification_claim.add_argument("--output")
    platform_envelope = sub.add_parser("evaluate-platform-envelope")
    platform_envelope.add_argument("envelope")
    platform_envelope.add_argument("--expected", required=True)
    platform_envelope.add_argument("--now")
    platform_envelope.add_argument("--output")
    benchmark_evidence = sub.add_parser("validate-benchmark-evidence")
    benchmark_evidence.add_argument("path")
    benchmark_evidence.add_argument("--expected-manifest-sha256")
    benchmark_evidence.add_argument("--expected-host-report-sha256")
    benchmark_evidence.add_argument("--output")
    build_dev_benchmark = sub.add_parser("build-development-benchmark-evidence")
    build_dev_benchmark.add_argument("--benchmark-id", required=True)
    build_dev_benchmark.add_argument("--manifest", required=True)
    build_dev_benchmark.add_argument("--host-report", required=True)
    build_dev_benchmark.add_argument("--output", required=True)
    audit_register = sub.add_parser("register-audit-key")
    audit_register.add_argument("--state-dir", required=True)
    audit_register.add_argument("--identity-id", required=True)
    audit_register.add_argument("--generation", type=int, required=True)
    audit_register.add_argument("--public-key", required=True)
    audit_register.add_argument("--policy-version", default="audit-checkpoint-policy-v1")
    audit_register.add_argument("--actor", required=True)
    audit_register.add_argument("--reason", required=True)
    audit_register.add_argument("--at")
    audit_create = sub.add_parser("create-audit-checkpoint")
    audit_create.add_argument("--state-dir", required=True)
    audit_create.add_argument("--identity-id", required=True)
    audit_create.add_argument("--generation", type=int, required=True)
    audit_create.add_argument("--private-key", required=True)
    audit_create.add_argument("--output", required=True)
    audit_create.add_argument("--at")
    audit_verify = sub.add_parser("verify-audit-checkpoint")
    audit_verify.add_argument("--state-dir", required=True)
    audit_verify.add_argument("path")
    backup_state = sub.add_parser("backup-state")
    backup_state.add_argument("--state-dir", required=True)
    backup_state.add_argument("--output", required=True)
    backup_state.add_argument("--retention-days", type=int, default=30)
    backup_state.add_argument("--legal-hold-id")
    backup_state.add_argument("--legal-hold-reason")
    backup_state.add_argument("--legal-hold-expires-at")
    backup_state.add_argument("--legal-hold-review-due-at")
    verify_backup = sub.add_parser("verify-backup")
    verify_backup.add_argument("path")
    backup_retention = sub.add_parser("backup-retention")
    backup_retention.add_argument("path")
    backup_retention.add_argument("--now")
    backup_delete = sub.add_parser("delete-expired-backup")
    backup_delete.add_argument("path")
    backup_delete.add_argument("--actor", required=True)
    backup_delete.add_argument("--now")
    backup_delete.add_argument("--receipt")
    restore_state = sub.add_parser("restore-state")
    restore_state.add_argument("path")
    restore_state.add_argument("--target-dir", required=True)
    restore_state.add_argument("--replace", action="store_true")
    restore_state.add_argument("--current-tombstone-journal")
    restore_state.add_argument("--actor", required=True)
    restore_state.add_argument("--reason", required=True)
    restore_state.add_argument("--target-node", default="local-node")
    restore_state.add_argument("--target-namespace")
    restore_state.add_argument("--policy-version", required=True)
    tombstone = sub.add_parser("write-tombstone-journal")
    tombstone.add_argument("--state-dir", required=True)
    tombstone.add_argument("--output", required=True)
    privacy_closure = sub.add_parser("build-privacy-closure")
    privacy_closure.add_argument("--state-dir", required=True)
    privacy_closure.add_argument("--root", default=".")
    privacy_closure.add_argument("--output", default="privacy-closure.json")
    privacy_verify = sub.add_parser("verify-privacy-closure")
    privacy_verify.add_argument("path")
    export_evidence = sub.add_parser("export-evidence")
    export_evidence.add_argument("--state-dir", required=True)
    export_evidence.add_argument("--request", required=True)
    export_evidence.add_argument("--output", required=True)
    verify_export = sub.add_parser("verify-export")
    verify_export.add_argument("path")
    time_eval = sub.add_parser("evaluate-time")
    time_eval.add_argument("path")
    time_eval.add_argument("--output")
    geo_validate = sub.add_parser("validate-geometry")
    geo_validate.add_argument("path")
    geo_validate.add_argument("--output")
    migrate_observation = sub.add_parser("migrate-observation")
    migrate_observation.add_argument("path")
    migrate_observation.add_argument("--policy", required=True)
    migrate_observation.add_argument("--output")
    media = sub.add_parser("sanitize-media")
    media.add_argument("path")
    media.add_argument("--media-type", required=True)
    media.add_argument("--output-dir", required=True)
    media.add_argument("--report")
    args = parser.parse_args()
    if args.command == "register-audit-key":
        engine = DeterministicScenarioEngine(state_dir=args.state_dir)
        public = load_public_key(args.public_key).public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        at = _parse_datetime(args.at) if args.at else datetime.now(timezone.utc)
        record = engine.key_lifecycle.register(
            identity_id=args.identity_id, generation=args.generation, purpose=KeyPurpose.AUDIT_SIGNING,
            public_key_raw=public, policy_version=args.policy_version, actor=args.actor, reason=args.reason,
            active_from=at, registered_at=at,
        )
        print(record.model_dump_json(indent=2))
        raise SystemExit(0)
    if args.command == "create-audit-checkpoint":
        engine = DeterministicScenarioEngine(state_dir=args.state_dir)
        private = load_private_key(args.private_key).private_bytes(
            serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption()
        )
        at = _parse_datetime(args.at) if args.at else datetime.now(timezone.utc)
        conformance = engine.incidents.authority_conformance()
        checkpoint = engine.audit.create(
            entries=engine.incidents.authority_journal(), authority_epoch_id=str(conformance["epoch_id"]),
            signer_identity_id=args.identity_id, signer_generation=args.generation, private_key_raw=private,
            created_at=at,
        )
        Path(args.output).write_text(checkpoint.model_dump_json(indent=2) + "\n", encoding="utf-8")
        print(args.output)
        raise SystemExit(0)
    if args.command == "verify-audit-checkpoint":
        engine = DeterministicScenarioEngine(state_dir=args.state_dir)
        checkpoint = AuditCheckpoint.model_validate_json(Path(args.path).read_text(encoding="utf-8"))
        result = engine.audit.verify(checkpoint, entries=engine.incidents.authority_journal())
        print(result.model_dump_json(indent=2))
        raise SystemExit(0 if result.valid else 1)
    if args.command == "sanitize-media":
        report, sanitized = BoundedMediaParser().parse_path(args.path, media_type=args.media_type)
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        payload = report.model_dump(mode="json")
        if sanitized is not None and report.output_sha256 is not None:
            output_path = output_dir / f"{report.output_sha256}.png"
            output_path.write_bytes(sanitized)
            payload["sanitized_path"] = str(output_path)
        if args.report:
            Path(args.report).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2, sort_keys=True))
        raise SystemExit(0 if report.status.value == "completed" else 2)
    if args.command == "evaluate-time":
        payload = json.loads(Path(args.path).read_text(encoding="utf-8"))
        observations = payload if isinstance(payload, list) else payload.get("sources", [payload])
        manager = TrustedTimeManager()
        snapshot = None
        for item in observations:
            snapshot = manager.update(TimeSourceObservation.model_validate(item))
        result = snapshot.model_dump(mode="json") if snapshot else manager.snapshot.model_dump(mode="json")
        if args.output:
            Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if result["display_time_allowed"] else 2)
    if args.command == "validate-geometry":
        payload = json.loads(Path(args.path).read_text(encoding="utf-8"))
        report = validate_geojson_geometry(
            payload["geometry"],
            source_crs=str(payload.get("source_crs", "EPSG:4326")),
            source_axis_order=str(payload.get("source_axis_order", "longitude_latitude")),
            transform_pipeline=str(payload.get("transform_pipeline", "identity:EPSG:4326")),
            max_coordinates=int(payload.get("max_coordinates", 10000)),
        )
        if args.output:
            Path(args.output).write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
        print(report.model_dump_json(indent=2))
        raise SystemExit(0 if report.decision.value == "valid" else 2)
    if args.command == "migrate-observation":
        payload = json.loads(Path(args.path).read_text(encoding="utf-8"))
        raw_policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))
        policy = LegacyObservationPolicy(
            source_id=raw_policy["source_id"],
            allowed_properties=frozenset(raw_policy["allowed_properties"]),
            property_aliases=dict(raw_policy.get("property_aliases", {})),
            allowed_units={key: frozenset(value) for key, value in raw_policy["allowed_units"].items()},
        )
        report = ObservationMigrator((policy,)).migrate(payload)
        if args.output:
            Path(args.output).write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
        print(report.model_dump_json(indent=2))
        raise SystemExit(0 if report.state in {"migrated", "unchanged"} else 2)
    if args.command == "backup-state":
        manager = StateBackupManager()
        path = manager.create(
            args.state_dir,
            args.output,
            retention_days=args.retention_days,
            legal_hold_id=args.legal_hold_id,
            legal_hold_reason=args.legal_hold_reason,
            legal_hold_expires_at=datetime.fromisoformat(args.legal_hold_expires_at) if args.legal_hold_expires_at else None,
            legal_hold_review_due_at=datetime.fromisoformat(args.legal_hold_review_due_at) if args.legal_hold_review_due_at else None,
        )
        print(json.dumps({"backup": str(path), "verification": manager.verify(path)}, indent=2, sort_keys=True))
        raise SystemExit(0)
    if args.command == "verify-backup":
        result = StateBackupManager().verify(args.path)
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if result["valid"] else 1)
    if args.command == "backup-retention":
        result = StateBackupManager().retention_decision(
            args.path, now=datetime.fromisoformat(args.now) if args.now else None
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if result["removable"] else 2)
    if args.command == "delete-expired-backup":
        result = StateBackupManager().delete_if_expired(
            args.path,
            now=datetime.fromisoformat(args.now) if args.now else None,
            actor=args.actor,
            receipt_path=args.receipt,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0)
    if args.command == "restore-state":
        from sentinel_edge.storage.restore_authorization import RestoreAuthorization
        result = StateBackupManager().restore(
            args.path, args.target_dir, replace=args.replace,
            current_tombstone_journal=args.current_tombstone_journal,
            authorization=RestoreAuthorization(actor=args.actor, reason=args.reason,
                target_node=args.target_node, target_namespace=args.target_namespace or Path(args.target_dir).name,
                policy_version=args.policy_version),
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0)
    if args.command == "write-tombstone-journal":
        engine = DeterministicScenarioEngine(state_dir=args.state_dir)
        journal = write_tombstone_journal(engine.evidence.store, args.output)
        print(journal.model_dump_json(indent=2))
        raise SystemExit(0)
    if args.command == "build-privacy-closure":
        engine = DeterministicScenarioEngine(state_dir=args.state_dir)
        path = write_privacy_closure(engine, repository_root=args.root, output=args.output)
        print(path)
        raise SystemExit(0)
    if args.command == "verify-privacy-closure":
        result = verify_privacy_closure(args.path)
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if result["valid"] else 1)
    if args.command == "export-evidence":
        engine = DeterministicScenarioEngine(state_dir=args.state_dir)
        payload = json.loads(Path(args.request).read_text(encoding="utf-8"))
        selections = tuple(EvidenceExportSelection.model_validate(item) for item in payload.get("selections", []))
        derivatives = tuple(DerivedArtifactSelection.model_validate(item) for item in payload.get("derivatives", []))
        manifest = engine.exports.create(args.output, selections=selections, derivatives=derivatives)
        result = engine.exports.verify(args.output)
        print(json.dumps({"manifest": manifest.model_dump(mode="json"), "verification": result}, indent=2, sort_keys=True))
        raise SystemExit(0 if result["valid"] else 1)
    if args.command == "verify-export":
        engine = DeterministicScenarioEngine()
        result = engine.exports.verify(args.path)
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if result["valid"] else 1)
    if args.command == "doctor":
        raise SystemExit(doctor())
    if args.command == "run-scenario":
        raise SystemExit(run_scenario(args.path, args.state_dir, args.public_key))
    if args.command == "benchmark":
        raise SystemExit(benchmark(args.path, args.iterations))
    if args.command == "benchmark-replay":
        raise SystemExit(benchmark_replay(args.path))
    if args.command == "after-event-review":
        raise SystemExit(after_event_review(args.path, args.state_dir, args.output))
    if args.command == "activate-configuration":
        raise SystemExit(activate_configuration(args.path, args.state_dir, args.fail_canary))
    if args.command == "build-manifest":
        print(write_manifest(args.root))
        raise SystemExit(0)
    if args.command == "build-release-candidate":
        raise SystemExit(build_candidate(args.root, args.state_dir, args.output))
    if args.command == "verify-release-candidate":
        raise SystemExit(verify_candidate(args.path, args.root))
    if args.command == "build-sbom":
        print(write_cyclonedx_sbom(args.root, args.output))
        raise SystemExit(0)
    if args.command == "build-third-party-inventory":
        print(write_third_party_inventory(args.root, args.output))
        raise SystemExit(0)
    if args.command == "build-third-party-notices":
        print(write_third_party_notices(args.root, args.output))
        raise SystemExit(0)
    if args.command == "build-provenance":
        print(write_provenance(args.root, args.output))
        raise SystemExit(0)
    if args.command == "verify-provenance":
        result = verify_provenance(args.path, args.root, expected_builder_id=args.expected_builder)
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if result["valid"] else 1)
    if args.command == "build-security-review":
        print(write_security_review(args.root, args.snapshot, args.output))
        raise SystemExit(0)
    if args.command == "verify-security-review":
        result = verify_security_review(args.path, args.sbom)
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if result["valid"] else 1)
    if args.command == "build-release-lock":
        print(write_release_lock(args.root, args.output))
        raise SystemExit(0)
    if args.command == "build-offline-wheelhouse":
        from packaging.tags import sys_tags
        capture = mirror_installed_resolution(args.lock, args.output_dir)
        report = verify_wheelhouse(args.lock, args.output_dir, compatible_tags={str(tag) for tag in sys_tags()}, install_rehearsal=True)
        Path(args.report).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"capture": capture, "verification": report}, indent=2, sort_keys=True))
        raise SystemExit(0 if report["release_eligible"] else 2)
    if args.command == "verify-offline-wheelhouse":
        from packaging.tags import sys_tags
        report = verify_wheelhouse(args.lock, args.wheelhouse, compatible_tags={str(tag) for tag in sys_tags()}, install_rehearsal=True)
        if args.report:
            Path(args.report).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2, sort_keys=True))
        raise SystemExit(0 if report["release_eligible"] else 2)
    if args.command == "verify-target-wheelhouse":
        report = verify_target_wheelhouse(args.lock, args.manifest, root=args.root, required_target_tags=args.target_tag)
        if args.report:
            Path(args.report).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2, sort_keys=True))
        raise SystemExit(0 if report["release_eligible"] else 2)
    if args.command == "sign-benchmark-plan":
        plan = BenchmarkAnalysisPlan.model_validate_json(Path(args.plan).read_text(encoding="utf-8"))
        signed = sign_analysis_plan(plan, load_private_key(args.private_key))
        Path(args.output).write_text(signed.model_dump_json(indent=2) + "\n", encoding="utf-8")
        print(args.output)
        raise SystemExit(0)
    if args.command == "verify-benchmark-plan":
        signed = SignedBenchmarkPlan.model_validate_json(Path(args.plan).read_text(encoding="utf-8"))
        result = verify_signed_plan(signed, load_public_key(args.public_key))
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if result["valid"] else 1)
    if args.command == "verify-benchmark-identities":
        raw = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        result = verify_file_identities(args.root, tuple(FileIdentitySpec.model_validate(item) for item in raw["items"]))
        if args.output:
            Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if result["measured_mode_allowed"] else 2)
    if args.command == "analyze-benchmark-execution":
        signed = SignedBenchmarkPlan.model_validate_json(Path(args.signed_plan).read_text(encoding="utf-8"))
        execution = BenchmarkExecutionRecord.model_validate_json(Path(args.execution).read_text(encoding="utf-8"))
        runtime_reports = tuple(json.loads(Path(path).read_text(encoding="utf-8")) for path in args.runtime_report)
        result = analyze_execution(
            signed,
            load_public_key(args.public_key),
            execution,
            network_report=json.loads(Path(args.network_report).read_text(encoding="utf-8")),
            host_report=json.loads(Path(args.host_report).read_text(encoding="utf-8")),
            runtime_qualifications=runtime_reports,
            wheelhouse_report=json.loads(Path(args.wheelhouse_report).read_text(encoding="utf-8")),
        )
        Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if result["target_measurement_claim_allowed"] else 2)
    if args.command == "probe-network-isolation":
        path = write_network_isolation_report(args.output)
        result = verify_network_isolation_report(path)
        print(json.dumps({"path": str(path), "verification": result}, indent=2, sort_keys=True))
        raise SystemExit(0 if result["release_eligible"] else 2)
    if args.command == "verify-network-isolation":
        result = verify_network_isolation_report(args.path)
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if result["valid"] else 1)
    if args.command == "build-reproducibility-report":
        print(write_reproducibility_report(args.root, args.output))
        raise SystemExit(0)
    if args.command == "verify-reproducibility-report":
        result = verify_reproducibility_report(args.path, args.root)
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if result["valid"] else 1)
    if args.command == "observe-host-trust":
        print(write_host_trust_report(args.output, require_secure_boot=args.require_secure_boot))
        raise SystemExit(0)
    if args.command == "verify-host-trust":
        result = verify_host_trust_report(args.path)
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if result["valid"] else 1)
    if args.command == "scan-toolchain":
        result = scan_toolchain_inventory(args.path)
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if result["release_eligible"] else 2)
    if args.command == "generate-bearer-token":
        print(generate_bearer_token())
        raise SystemExit(0)
    if args.command == "generate-signing-key":
        private, public = generate_keypair(args.private, args.public)
        print(json.dumps({"private": str(private), "public": str(public)}, indent=2, sort_keys=True))
        raise SystemExit(0)
    if args.command == "sign-release-candidate":
        print(sign_release_candidate(args.candidate, load_private_key(args.private_key), args.output))
        raise SystemExit(0)
    if args.command == "verify-release-signature":
        result = verify_release_signature(args.candidate, args.signature, load_public_key(args.public_key))
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if result["valid"] else 1)
    if args.command == "build-update-bundle":
        path = build_update_bundle(
            args.output,
            source_root=args.root,
            target_paths=args.target,
            private_key=load_private_key(args.private_key),
            bundle_id=args.bundle_id,
            version=args.update_version,
            created_at=_parse_datetime(args.created_at),
            expires_at=_parse_datetime(args.expires_at),
            compatible_min_version=args.compatible_min_version,
            compatible_max_version=args.compatible_max_version,
        )
        print(path)
        raise SystemExit(0)
    if args.command in {"verify-update-bundle", "stage-update-bundle"}:
        manager = OfflineUpdateManager(
            args.state_dir,
            load_public_key(args.public_key),
            current_project_version=__version__,
            mode=RuntimeMode(args.mode),
        )
        now = _parse_datetime(args.now) if args.now else None
        if args.command == "verify-update-bundle":
            metadata, verification = manager.verify(args.bundle, now=now)
            print(json.dumps({"metadata": metadata.model_dump(mode="json"), "verification": verification.model_dump(mode="json")}, indent=2, sort_keys=True))
        else:
            path, verification = manager.stage(args.bundle, now=now)
            print(json.dumps({"staged_path": str(path), "verification": verification.model_dump(mode="json")}, indent=2, sort_keys=True))
        raise SystemExit(0)
    if args.command == "observe-host":
        report = observe_host()
        if args.output:
            write_json_report(args.output, report)
        print(report.model_dump_json(indent=2))
        raise SystemExit(0)
    if args.command == "qualify-host":
        report = qualify_host(load_host_profile(args.profile))
        if args.output:
            write_json_report(args.output, report)
        print(report.model_dump_json(indent=2))
        raise SystemExit(0 if report.host_profile_match else 2)
    if args.command == "commission-imu":
        report = commission_imu(
            args.path,
            source_id=args.source_id,
            requested_rate_hz=args.rate_hz,
            minimum_samples=args.minimum_samples,
        )
        if args.output:
            write_json_report(args.output, report)
        print(report.model_dump_json(indent=2))
        raise SystemExit(0 if report.state.value in {"tested", "field_qualified", "target_qualified"} else 2)
    if args.command == "commission-camera":
        report = commission_camera(
            args.path,
            source_id=args.source_id,
            requested_fps=args.fps,
            minimum_frames=args.minimum_frames,
        )
        if args.output:
            write_json_report(args.output, report)
        print(report.model_dump_json(indent=2))
        raise SystemExit(0 if report.state.value in {"tested", "field_qualified", "target_qualified"} else 2)
    if args.command == "qualify-model-quality":
        report = qualify_model_quality(
            load_model_quality_manifest(args.manifest),
            root=args.root,
            now=_parse_datetime(args.now) if args.now else None,
        )
        if args.output:
            write_json_report(args.output, report)
        print(report.model_dump_json(indent=2))
        raise SystemExit(0 if report.state.value in {"tested", "target_qualified"} else 2)
    if args.command == "qualify-source":
        report = qualify_source(
            load_source_policy(args.policy),
            load_source_observation(args.observation),
            now=_parse_datetime(args.now) if args.now else None,
        )
        if args.output:
            write_json_report(args.output, report)
        print(report.model_dump_json(indent=2))
        raise SystemExit(0 if report.decision_influence_allowed else 2)
    if args.command == "summarize-sources":
        from sentinel_edge.domain.models import SourceQualificationReport
        reports = [SourceQualificationReport.model_validate_json(Path(path).read_text(encoding="utf-8")) for path in args.report]
        payload = summarize_sources(reports)
        write_json_report(args.output, payload)
        print(args.output)
        raise SystemExit(0 if payload["h0_zero_live_source_valid"] else 2)
    if args.command == "qualify-runtime-profile":
        host_report = None
        if args.host_report:
            host_report = HostQualificationReport.model_validate_json(Path(args.host_report).read_text(encoding="utf-8"))
        report = qualify_runtime_profile(
            load_runtime_profile(args.manifest),
            root=args.root,
            host_report=host_report,
        )
        if args.output:
            write_json_report(args.output, report)
        print(report.model_dump_json(indent=2))
        raise SystemExit(0 if report.state.value in {"tested", "field_qualified", "target_qualified"} else 2)
    if args.command == "inspect-onnx-model":
        report = inspect_onnx_graph(args.path)
        if args.output:
            write_json_report(args.output, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        raise SystemExit(0)
    if args.command == "admit-model-package":
        manifest = ModelPackageManifest.model_validate_json(Path(args.manifest).read_text(encoding="utf-8"))
        context = RuntimeAdmissionContext.model_validate_json(Path(args.runtime_context).read_text(encoding="utf-8"))
        issue_report = json.loads(Path(args.runtime_issues).read_text(encoding="utf-8"))
        report = admit_model_package(
            manifest, root=args.root, runtime=context, runtime_issue_evaluation=issue_report,
            now=_parse_datetime(args.now) if args.now else None,
        )
        if args.output:
            write_json_report(args.output, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        raise SystemExit(0 if report["admission_passed"] else 2)
    if args.command == "scan-model-execution-boundary":
        report = scan_model_execution_boundaries(args.root)
        if args.output:
            write_json_report(args.output, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        raise SystemExit(0 if report["valid"] else 2)
    if args.command == "evaluate-signal-chain":
        envelope = SignedSignalChainProfile.model_validate_json(Path(args.profile).read_text(encoding="utf-8"))
        observation = SignalChainObservation.model_validate_json(Path(args.observation).read_text(encoding="utf-8"))
        report = evaluate_signal_chain(
            envelope, load_public_key(args.public_key), observation, model_profile_id=args.model_profile_id,
            now=_parse_datetime(args.now) if args.now else None,
        )
        if args.output:
            write_json_report(args.output, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        raise SystemExit(0 if report["compatibility_passed"] else 2)
    if args.command == "evaluate-site-commissioning":
        envelope = SignedSiteCommissioningRecord.model_validate_json(Path(args.record).read_text(encoding="utf-8"))
        signal_report = json.loads(Path(args.signal_chain_report).read_text(encoding="utf-8"))
        report = evaluate_site_commissioning(
            envelope, load_public_key(args.public_key), signal_chain_report=signal_report,
            current_sensor_identity=args.sensor_identity, current_configuration_sha256=args.configuration_sha256,
            current_mounting_or_pose=args.mounting_or_pose, current_model_profile_id=args.model_profile_id,
            now=_parse_datetime(args.now) if args.now else None,
        )
        if args.output:
            write_json_report(args.output, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        raise SystemExit(0 if not report["failures"] else 2)
    if args.command == "evaluate-qualification-window":
        window = QualificationEvidenceWindow.model_validate_json(Path(args.window).read_text(encoding="utf-8"))
        report = evaluate_evidence_window(window, now=_parse_datetime(args.now) if args.now else None)
        if args.output:
            write_json_report(args.output, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        raise SystemExit(0 if report["claim_allowed"] else 2)
    if args.command == "evaluate-qualification-claim":
        claim = QualificationClaim.model_validate_json(Path(args.claim).read_text(encoding="utf-8"))
        evaluations = [json.loads(Path(path).read_text(encoding="utf-8")) for path in args.evaluation]
        report = enforce_claim_ceiling(claim, evaluations)
        if args.output:
            write_json_report(args.output, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        raise SystemExit(0 if report["allowed"] else 2)
    if args.command == "evaluate-platform-envelope":
        envelope = PlatformRuntimeEnvelope.model_validate_json(Path(args.envelope).read_text(encoding="utf-8"))
        expected = json.loads(Path(args.expected).read_text(encoding="utf-8"))
        report = evaluate_platform_runtime_envelope(envelope, expected=expected, now=_parse_datetime(args.now) if args.now else None)
        if args.output:
            write_json_report(args.output, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        raise SystemExit(0 if report["target_qualified"] else 2)
    if args.command == "validate-benchmark-evidence":
        report = validate_benchmark_evidence(
            args.path,
            expected_manifest_sha256=args.expected_manifest_sha256,
            expected_host_report_sha256=args.expected_host_report_sha256,
        )
        if args.output:
            write_json_report(args.output, report)
        print(report.model_dump_json(indent=2))
        raise SystemExit(0 if report.target_measurement_claim_allowed else 2)
    if args.command == "build-development-benchmark-evidence":
        payload = build_development_benchmark_evidence(
            benchmark_id=args.benchmark_id,
            benchmark_manifest_path=args.manifest,
            host_report_path=args.host_report,
        )
        write_json_report(args.output, payload)
        print(args.output)
        raise SystemExit(0)
    if args.command == "activate-staged-update":
        manager = OfflineUpdateManager(
            args.state_dir,
            load_public_key(args.public_key),
            current_project_version=__version__,
            mode=RuntimeMode.FIELD_LAB,
        )
        result = manager.activate(args.staged_path, self_test=_update_self_test, now=_parse_datetime(args.now) if args.now else None)
        print(result.model_dump_json(indent=2))
        raise SystemExit(0 if result.state.value == "activated" else 2)
    if args.command == "serve":
        import uvicorn

        auth = AuthManager.development() if args.auth_mode == "development" else AuthManager.from_environment()
        uvicorn.run(create_app(auth_manager=auth), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
