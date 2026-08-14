from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from packaging.tags import sys_tags

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sentinel_edge.qualification import write_host_trust_report, write_network_isolation_report, verify_network_isolation_report
from sentinel_edge.release import (
    AdvisoryCoveragePolicy,
    apply_coverage_policy,
    build_independent_build_report,
    build_release_governance_report,
    build_security_review,
    build_attestation,
    mirror_installed_resolution,
    scan_toolchain_inventory,
    verify_reproducibility_report,
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


def _write_public(path: Path, key: Ed25519PrivateKey) -> None:
    path.write_bytes(
        key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )


def build(root: Path) -> dict:
    evidence = root / "evidence"
    evidence.mkdir(exist_ok=True)

    lock = write_release_lock(root, root / "requirements-release.lock.json")
    wheelhouse = root / "artifacts" / "wheelhouse"
    for old in wheelhouse.glob("*.whl") if wheelhouse.exists() else []:
        old.unlink()
    capture = mirror_installed_resolution(lock, wheelhouse)
    wheel_report = verify_wheelhouse(
        lock,
        wheelhouse,
        compatible_tags={str(tag) for tag in sys_tags()},
        install_rehearsal=True,
    )
    (root / "wheelhouse-report.json").write_text(json.dumps(wheel_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    network_path = write_network_isolation_report(root / "network-isolation-report.json")
    repro_path = write_reproducibility_report(root, root / "reproducibility-report.json")
    host_path = write_host_trust_report(root / "host-trust-report.json")

    write_cyclonedx_sbom(root, root / "sbom.cdx.json")
    write_third_party_inventory(root, root / "third-party-inventory.json")
    write_third_party_notices(root, root / "THIRD_PARTY_NOTICES.md")
    sbom = json.loads((root / "sbom.cdx.json").read_text(encoding="utf-8"))
    snapshots = [
        root / "fixtures/security/advisory-osv-bounded.json",
        root / "fixtures/security/advisory-github_advisory-bounded.json",
        root / "fixtures/security/advisory-cisa_kev-bounded.json",
        root / "fixtures/security/advisory-vendor-bounded.json",
    ]
    review = build_security_review(sbom, [load_advisory_snapshot(path) for path in snapshots])
    review = apply_coverage_policy(review, AdvisoryCoveragePolicy(), toolchain_review=scan_toolchain_inventory([]))
    (root / "security-review.json").write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    repro = json.loads(repro_path.read_text(encoding="utf-8"))
    source_digest = repro["source_members_digest"]
    artifact_digest = repro["artifact_classes"][0]["build_a"]["sha256"]
    builder_a = Ed25519PrivateKey.generate()
    builder_b = Ed25519PrivateKey.generate()
    host_fingerprint = sha256_bytes(canonical_json_bytes({"node": platform.node(), "machine": platform.machine(), "system": platform.system()}))
    attestations = [
        build_attestation(
            builder_id="sentinel-local-builder-a",
            host_fingerprint=host_fingerprint,
            environment_digest=sha256_bytes(b"builder-environment-a"),
            source_digest=source_digest,
            artifact_digest=artifact_digest,
            private_key=builder_a,
        ),
        build_attestation(
            builder_id="sentinel-local-builder-b",
            host_fingerprint=host_fingerprint,
            environment_digest=sha256_bytes(b"builder-environment-b"),
            source_digest=source_digest,
            artifact_digest=artifact_digest,
            private_key=builder_b,
        ),
    ]
    public_keys = {
        key_id(builder_a.public_key()): builder_a.public_key(),
        key_id(builder_b.public_key()): builder_b.public_key(),
    }
    independent = build_independent_build_report(attestations, public_keys)
    write_independent_build_report(root / "independent-build-report.json", independent)
    _write_public(evidence / "v0.17.0-builder-a-public.pem", builder_a)
    _write_public(evidence / "v0.17.0-builder-b-public.pem", builder_b)

    release_public = load_pem_public_key((evidence / "v0.17.0-release-public.pem").read_bytes())
    release_key_id = key_id(release_public)
    credential_profile = {
        "schema": "sentinel-edge-release-credential-profile/1.0",
        "private_key_storage": "external_offline_key",
        "development_bearer_tokens_present": False,
        "rotation_tested": True,
        "purpose_key_ids": {
            "release": release_key_id,
            "audit": "audit-key-v1",
            "update": "update-key-v1",
            "boot": "boot-key-unconfigured",
        },
        "evidence": ["tests/test_release_closure_v017.py"],
    }
    governance = build_release_governance_report(
        packets=[],
        reviewer_public_keys={},
        builder_ids={"sentinel-local-builder-a", "sentinel-local-builder-b"},
        release_signer_key_id=release_key_id,
        credential_profile=credential_profile,
    )
    write_release_governance_report(root / "release-governance-report.json", governance)

    base = {
        "schema": "sentinel-edge-v017-evidence/1.0",
        "wheelhouse": {
            "path": "wheelhouse-report.json",
            "sha256": sha256_file(root / "wheelhouse-report.json"),
            "capture_complete": capture["complete"],
            "wheel_count": wheel_report["manifest"]["wheel_count"],
            "offline_install_rehearsal": wheel_report["install_rehearsal"],
            "release_eligible_for_current_platform": wheel_report["release_eligible"],
        },
        "network_isolation": {
            "path": "network-isolation-report.json",
            "sha256": sha256_file(network_path),
            "verification": verify_network_isolation_report(network_path),
        },
        "reproducibility": {
            "path": "reproducibility-report.json",
            "sha256": sha256_file(repro_path),
            "verification": verify_reproducibility_report(repro_path, root),
        },
        "independent_build": {
            "path": "independent-build-report.json",
            "sha256": sha256_file(root / "independent-build-report.json"),
            "independent": independent["independent"],
            "failures": independent["failures"],
        },
        "release_governance": {
            "path": "release-governance-report.json",
            "sha256": sha256_file(root / "release-governance-report.json"),
            "release_credentials_proven": governance["release_credentials_proven"],
            "independent_reviews_complete": governance["independent_reviews_complete"],
            "failures": governance["failures"],
        },
        "host_trust": {"path": "host-trust-report.json", "sha256": sha256_file(host_path)},
        "security_review": {
            "path": "security-review.json",
            "sha256": sha256_file(root / "security-review.json"),
            "release_eligible": review["release_eligible"],
            "coverage_failures": review.get("coverage", {}).get("failures", []),
        },
        "limitations": [
            "The wheelhouse contains deterministic repacks of the current x86-64 installed environment, not publisher-original Arm64 wheels.",
            "The network namespace probe passed on this development host but is not Raspberry Pi benchmark-run evidence.",
            "Both builder attestations were produced on one host, so independent-builder closure remains false.",
            "Release credentials are purpose-separated and external by profile, but independent security/privacy/accessibility reviews are absent.",
            "No target-device qualification or release admission is claimed.",
        ],
    }
    return {**base, "receipt_sha256": sha256_bytes(canonical_json_bytes(base))}


def main() -> int:
    payload = build(ROOT)
    output = ROOT / "evidence/v0.17.0-wheelhouse-network-governance.json"
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
