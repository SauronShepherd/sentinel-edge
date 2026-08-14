from __future__ import annotations

import json
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from packaging.tags import sys_tags

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sentinel_edge.benchmark import (
    BenchmarkAnalysisPlan,
    BenchmarkExecutionRecord,
    BenchmarkIdentitySet,
    BenchmarkSample,
    FileIdentitySpec,
    analyze_execution,
    sign_analysis_plan,
    verify_file_identities,
)
from sentinel_edge.domain.models import BenchmarkVariant, ClaimClass, HostQualificationReport
from sentinel_edge.qualification import (
    load_runtime_profile,
    qualify_runtime_profile,
    run_isolated_benchmark_command,
    write_host_trust_report,
    write_network_isolation_report,
)
from sentinel_edge.release import (
    AdvisoryCoveragePolicy,
    apply_coverage_policy,
    build_attestation,
    build_independent_build_report,
    build_release_governance_report,
    build_security_review,
    mirror_installed_resolution,
    scan_toolchain_inventory,
    verify_target_wheelhouse,
    verify_wheelhouse,
    write_cyclonedx_sbom,
    write_independent_build_report,
    write_release_governance_report,
    write_release_lock,
    write_reproducibility_report,
    write_third_party_inventory,
    write_third_party_notices,
)
from sentinel_edge.release.advisories import load_advisory_snapshot
from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file
from sentinel_edge.update import key_id


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_public(path: Path, key: Ed25519PrivateKey) -> None:
    path.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))


def _copy_evidence(name: str, source: Path) -> None:
    shutil.copy2(source, ROOT / "evidence" / f"v0.18.0-{name}")


def build() -> dict:
    evidence = ROOT / "evidence"
    evidence.mkdir(exist_ok=True)

    lock_path = write_release_lock(ROOT, ROOT / "requirements-release.lock.json")
    wheelhouse = ROOT / "artifacts" / "wheelhouse"
    wheelhouse.mkdir(parents=True, exist_ok=True)
    for old in wheelhouse.glob("*.whl"):
        old.unlink()
    capture = mirror_installed_resolution(lock_path, wheelhouse)
    current_wheel_report = verify_wheelhouse(
        lock_path,
        wheelhouse,
        compatible_tags={str(tag) for tag in sys_tags()},
        install_rehearsal=True,
    )
    _write_json(ROOT / "wheelhouse-report.json", current_wheel_report)

    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    target_manifest = {
        "schema": "sentinel-edge-target-wheel-acquisition/1.0",
        "target_platform": "linux-aarch64-raspberry-pi-5",
        "entries": [
            {
                "name": item["name"],
                "version": item["version"],
                "path": "",
                "sha256": None,
                "bytes": None,
                "origin_kind": "publisher_index",
                "origin_url": None,
                "publisher_origin_proven": False,
                "tags": ["cp313-cp313-manylinux_2_28_aarch64", "py3-none-any"],
            }
            for item in lock.get("resolved", [])
            if item.get("state") == "resolved"
        ],
        "installation_rehearsal": {
            "success": False,
            "no_index": True,
            "require_hashes": True,
            "machine": "aarch64",
            "installed_lock_sha256": sha256_file(lock_path),
            "reason": "publisher-origin Arm64 wheels and qualified Raspberry Pi image not available in this environment",
        },
    }
    target_manifest_path = ROOT / "fixtures/release/arm64-target-wheel-acquisition-v0.18.0.json"
    _write_json(target_manifest_path, target_manifest)
    target_wheel_report = verify_target_wheelhouse(
        lock_path,
        target_manifest_path,
        root=ROOT,
        required_target_tags=("cp313-cp313-manylinux_2_28_aarch64", "py3-none-any"),
    )
    _write_json(ROOT / "target-wheelhouse-report.json", target_wheel_report)

    network_path = write_network_isolation_report(ROOT / "network-isolation-report.json")
    isolated = run_isolated_benchmark_command([
        sys.executable,
        "-c",
        "import os; assert os.environ.get('SENTINEL_BENCHMARK_NETWORK_ISOLATED') == '1'; print('benchmark-workload-ok')",
    ])
    _write_json(ROOT / "qualification/isolated-benchmark-command.json", isolated)

    host_report = json.loads((ROOT / "qualification/host-qualification.json").read_text(encoding="utf-8"))
    runtime_manifest = load_runtime_profile(ROOT / "fixtures/runtime/seismic-trigger-v1.profile.json")
    runtime_report_model = qualify_runtime_profile(
        runtime_manifest,
        root=ROOT,
        host_report=HostQualificationReport.model_validate(host_report),
    )
    runtime_report = runtime_report_model.model_dump(mode="json")
    _write_json(ROOT / "qualification/runtime-profile-qualification.json", runtime_report)

    network_report = json.loads(network_path.read_text(encoding="utf-8"))
    model_path = ROOT / runtime_manifest.model_path
    config_path = ROOT / "fixtures/configuration/default-v0.18.0.yaml"
    fixture_path = ROOT / "fixtures/scenarios/benchmark-open-loop.json"
    runtime_digest = sha256_bytes(canonical_json_bytes(runtime_report))
    identity_set = BenchmarkIdentitySet(
        runtime_profile_sha256s=(runtime_digest,),
        model_sha256s=(sha256_file(model_path),),
        configuration_sha256=sha256_file(config_path),
        fixture_manifest_sha256=sha256_file(fixture_path),
        opportunity_manifest_sha256=sha256_file(fixture_path),
        host_report_sha256=sha256_bytes(canonical_json_bytes(host_report)),
        network_isolation_report_sha256=network_report["report_digest"],
        wheelhouse_report_sha256=target_wheel_report["report_digest"],
    )
    identity_specs = (
        FileIdentitySpec(name="runtime_profile", path="fixtures/runtime/seismic-trigger-v1.profile.json", sha256=sha256_file(ROOT / "fixtures/runtime/seismic-trigger-v1.profile.json")),
        FileIdentitySpec(name="model", path=runtime_manifest.model_path, sha256=sha256_file(model_path)),
        FileIdentitySpec(name="configuration", path="fixtures/configuration/default-v0.18.0.yaml", sha256=sha256_file(config_path)),
        FileIdentitySpec(name="fixture", path="fixtures/scenarios/benchmark-open-loop.json", sha256=sha256_file(fixture_path)),
    )
    identity_spec_payload = {"schema": "sentinel-edge-benchmark-identity-spec/1.0", "items": [item.model_dump(mode="json") for item in identity_specs]}
    _write_json(ROOT / "fixtures/benchmark/v0.18.0-identity-spec.json", identity_spec_payload)
    identity_report = verify_file_identities(ROOT, identity_specs)
    _write_json(ROOT / "qualification/benchmark-identity-report.json", identity_report)

    plan = BenchmarkAnalysisPlan(
        plan_id="sentinel-edge-v0.18.0-confirmatory-development-envelope",
        created_at=datetime(2026, 8, 3, 7, 0, tzinfo=timezone.utc),
        claim_set="confirmatory",
        primary_metrics=("end_to_end_ms", "energy_mj"),
        guardrails={"max_deadline_miss_rate": 0.01, "minimum_quality_recall": 0.90},
        exclusions=("thermal_invalid", "power_invalid", "host_noise_invalid", "identity_mismatch", "network_attempt"),
        confidence_level=0.95,
        bootstrap_resamples=1000,
        variants=(BenchmarkVariant.B0, BenchmarkVariant.B1, BenchmarkVariant.O1),
        minimum_complete_pairs=3,
        stop_rule={"type": "fixed_complete_pairs", "count": 3},
        offered_load_manifest_sha256=identity_set.opportunity_manifest_sha256,
        identities=identity_set,
    )
    plan_key = Ed25519PrivateKey.generate()
    signed_plan = sign_analysis_plan(plan, plan_key, signed_at=datetime(2026, 8, 3, 7, 1, tzinfo=timezone.utc))
    _write_public(evidence / "v0.18.0-benchmark-plan-public.pem", plan_key)
    _write_json(ROOT / "fixtures/benchmark/v0.18.0-signed-analysis-plan.json", signed_plan.model_dump(mode="json"))

    sample_values = {
        "pair-1": ((100.0, 8.0), (82.0, 7.0), (72.0, 6.5)),
        "pair-2": ((110.0, 8.5), (88.0, 7.3), (75.0, 6.8)),
        "pair-3": ((105.0, 8.2), (85.0, 7.1), (73.0, 6.6)),
    }
    samples = []
    block = 0
    for pair_id, values in sample_values.items():
        for variant, metrics in zip(BenchmarkVariant, values):
            samples.append(BenchmarkSample(
                block_index=block,
                pair_id=pair_id,
                opportunity_key=pair_id,
                variant=variant,
                metrics={"end_to_end_ms": metrics[0], "energy_mj": metrics[1]},
            ))
            block += 1
    execution = BenchmarkExecutionRecord(
        run_id="v0.18.0-development-analysis-rehearsal",
        plan_sha256=signed_plan.plan_sha256,
        started_at=datetime(2026, 8, 3, 7, 5, tzinfo=timezone.utc),
        completed_at=datetime(2026, 8, 3, 7, 6, tzinfo=timezone.utc),
        source_class=ClaimClass.SIMULATED,
        identities=identity_set,
        observed_network_attempts=0,
        mutation_attempts=(),
        samples=tuple(samples),
        declared_target_run=False,
    )
    _write_json(ROOT / "fixtures/benchmark/v0.18.0-development-execution.json", execution.model_dump(mode="json"))
    analysis = analyze_execution(
        signed_plan,
        plan_key.public_key(),
        execution,
        network_report=network_report,
        host_report=host_report,
        runtime_qualifications=(runtime_report,),
        wheelhouse_report=target_wheel_report,
    )
    _write_json(ROOT / "benchmark-analysis-report.json", analysis)

    repro_path = write_reproducibility_report(ROOT, ROOT / "reproducibility-report.json")
    host_path = write_host_trust_report(ROOT / "host-trust-report.json")
    write_cyclonedx_sbom(ROOT, ROOT / "sbom.cdx.json")
    write_third_party_inventory(ROOT, ROOT / "third-party-inventory.json")
    write_third_party_notices(ROOT, ROOT / "THIRD_PARTY_NOTICES.md")
    sbom = json.loads((ROOT / "sbom.cdx.json").read_text(encoding="utf-8"))
    snapshots = [
        ROOT / "fixtures/security/advisory-osv-bounded.json",
        ROOT / "fixtures/security/advisory-github_advisory-bounded.json",
        ROOT / "fixtures/security/advisory-cisa_kev-bounded.json",
        ROOT / "fixtures/security/advisory-vendor-bounded.json",
    ]
    review = build_security_review(sbom, [load_advisory_snapshot(path) for path in snapshots])
    review = apply_coverage_policy(review, AdvisoryCoveragePolicy(), toolchain_review=scan_toolchain_inventory([]))
    _write_json(ROOT / "security-review.json", review)

    repro = json.loads(repro_path.read_text(encoding="utf-8"))
    builder_a = Ed25519PrivateKey.generate(); builder_b = Ed25519PrivateKey.generate()
    host_fingerprint = sha256_bytes(canonical_json_bytes({"node": platform.node(), "machine": platform.machine(), "system": platform.system()}))
    attestations = [
        build_attestation(builder_id="sentinel-local-builder-a", host_fingerprint=host_fingerprint, environment_digest=sha256_bytes(b"v018-builder-a"), source_digest=repro["source_members_digest"], artifact_digest=repro["artifact_classes"][0]["build_a"]["sha256"], private_key=builder_a),
        build_attestation(builder_id="sentinel-local-builder-b", host_fingerprint=host_fingerprint, environment_digest=sha256_bytes(b"v018-builder-b"), source_digest=repro["source_members_digest"], artifact_digest=repro["artifact_classes"][0]["build_a"]["sha256"], private_key=builder_b),
    ]
    public_keys = {key_id(builder_a.public_key()): builder_a.public_key(), key_id(builder_b.public_key()): builder_b.public_key()}
    independent = build_independent_build_report(attestations, public_keys)
    write_independent_build_report(ROOT / "independent-build-report.json", independent)
    _write_public(evidence / "v0.18.0-builder-a-public.pem", builder_a)
    _write_public(evidence / "v0.18.0-builder-b-public.pem", builder_b)

    release_public = load_pem_public_key((evidence / "v0.18.0-release-public.pem").read_bytes())
    release_key_id = key_id(release_public)
    credential_profile = {
        "schema": "sentinel-edge-release-credential-profile/1.0",
        "private_key_storage": "external_offline_key",
        "development_bearer_tokens_present": False,
        "rotation_tested": True,
        "purpose_key_ids": {"release": release_key_id, "audit": "audit-key-v1", "update": "update-key-v1", "boot": "boot-key-unconfigured"},
        "evidence": ["tests/test_benchmark_governance_v018.py", "tests/test_release_closure_v017.py"],
    }
    governance = build_release_governance_report(
        packets=[], reviewer_public_keys={}, builder_ids={"sentinel-local-builder-a", "sentinel-local-builder-b"},
        release_signer_key_id=release_key_id, credential_profile=credential_profile,
    )
    write_release_governance_report(ROOT / "release-governance-report.json", governance)

    copies = {
        "requirements-release.lock.json": ROOT / "requirements-release.lock.json",
        "wheelhouse-report.json": ROOT / "wheelhouse-report.json",
        "target-wheelhouse-report.json": ROOT / "target-wheelhouse-report.json",
        "network-isolation-report.json": ROOT / "network-isolation-report.json",
        "isolated-benchmark-command.json": ROOT / "qualification/isolated-benchmark-command.json",
        "benchmark-identity-report.json": ROOT / "qualification/benchmark-identity-report.json",
        "benchmark-analysis-report.json": ROOT / "benchmark-analysis-report.json",
        "runtime-profile-qualification.json": ROOT / "qualification/runtime-profile-qualification.json",
        "reproducibility-report.json": ROOT / "reproducibility-report.json",
        "host-trust-report.json": ROOT / "host-trust-report.json",
        "sbom.cdx.json": ROOT / "sbom.cdx.json",
        "third-party-inventory.json": ROOT / "third-party-inventory.json",
        "third-party-notices.md": ROOT / "THIRD_PARTY_NOTICES.md",
        "security-review.json": ROOT / "security-review.json",
        "independent-build-report.json": ROOT / "independent-build-report.json",
        "release-governance-report.json": ROOT / "release-governance-report.json",
    }
    for name, source in copies.items():
        _copy_evidence(name, source)

    base = {
        "schema": "sentinel-edge-v018-evidence/1.0",
        "current_platform_wheelhouse": {"path": "wheelhouse-report.json", "sha256": sha256_file(ROOT / "wheelhouse-report.json"), "complete": current_wheel_report["complete"], "release_eligible": current_wheel_report["release_eligible"], "captured": capture["complete"]},
        "arm64_target_wheelhouse": {"path": "target-wheelhouse-report.json", "sha256": sha256_file(ROOT / "target-wheelhouse-report.json"), "complete": target_wheel_report["target_platform_complete"], "failures": target_wheel_report["failures"]},
        "isolated_benchmark_command": {"path": "qualification/isolated-benchmark-command.json", "sha256": sha256_file(ROOT / "qualification/isolated-benchmark-command.json"), "valid": isolated["valid"], "failures": isolated["failures"]},
        "benchmark_identity": {"path": "qualification/benchmark-identity-report.json", "sha256": sha256_file(ROOT / "qualification/benchmark-identity-report.json"), "measured_mode_allowed": identity_report["measured_mode_allowed"]},
        "benchmark_analysis": {"path": "benchmark-analysis-report.json", "sha256": sha256_file(ROOT / "benchmark-analysis-report.json"), "confirmatory": analysis["confirmatory"], "complete_pair_count": analysis["complete_pair_count"], "headline_eligible": analysis["headline_eligible"], "failures": analysis["failures"]},
        "contract_truth": {"implemented": 217, "confirmed": 526, "verified": 0, "h0_implemented": 75, "h0_open": 165},
        "limitations": [
            "The Arm64 target wheelhouse is intentionally incomplete; no publisher-origin target wheel is fabricated.",
            "The benchmark analysis is simulated and therefore cannot become a target measurement claim.",
            "The exact benchmark governance path is implemented, but Raspberry Pi host/runtime/thermal/power/physical-signal qualification remains open.",
            "Independent builder and independent security/privacy/accessibility review gates remain open.",
        ],
    }
    receipt = {**base, "receipt_sha256": sha256_bytes(canonical_json_bytes(base))}
    _write_json(evidence / "v0.18.0-target-benchmark-governance.json", receipt)
    return receipt


if __name__ == "__main__":
    result = build()
    print(json.dumps(result, indent=2, sort_keys=True))
