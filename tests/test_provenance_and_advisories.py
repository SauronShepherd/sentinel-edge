import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sentinel_edge.release import (
    VexDecision,
    build_cyclonedx_sbom,
    build_provenance,
    build_security_review,
    verify_provenance,
    verify_security_review,
    write_provenance,
)
from sentinel_edge.release.advisories import load_advisory_snapshot
from sentinel_edge.security import sha256_file


def test_provenance_binds_materials_environment_and_does_not_overclaim(tmp_path: Path) -> None:
    root = Path.cwd()
    provenance = build_provenance(root)
    assert provenance["predicateType"] == "https://slsa.dev/provenance/v1"
    assert provenance["subject"][0]["digest"]["sha256"]
    internal = provenance["predicate"]["buildDefinition"]["internalParameters"]
    assert internal["network_access"] == "dependency_install_rehearsed_no_index; source_bundle_python_guard; benchmark_namespace_probe_bound_separately"
    assert internal["hermeticity"] == "not_claimed"
    assert internal["reproducibility_class"] == "provenance_only"
    assert provenance["sentinel_edge"]["secret_scan_passed"] is True
    path = write_provenance(root, tmp_path / "provenance.json")
    assert verify_provenance(path, root)["valid"] is True


def test_provenance_detects_subject_tamper(tmp_path: Path) -> None:
    root = Path.cwd()
    path = write_provenance(root, tmp_path / "provenance.json")
    payload = json.loads(path.read_text())
    payload["sentinel_edge"]["subject_digest"] = "0" * 64
    path.write_text(json.dumps(payload))
    result = verify_provenance(path, root)
    assert result["valid"] is False
    assert "source_subject_digest_mismatch" in result["failures"]


def test_provenance_policy_rejects_unexpected_builder(tmp_path: Path) -> None:
    root = Path.cwd()
    path = write_provenance(root, tmp_path / "provenance.json")
    result = verify_provenance(path, root, expected_builder_id="different-builder")
    assert result["valid"] is False
    assert "unexpected_builder_identity" in result["failures"]


def _synthetic_sbom(version: str) -> dict:
    sbom = build_cyclonedx_sbom(Path.cwd())
    component = next(item for item in sbom["components"] if item["name"].lower() == "fastapi")
    component["version"] = version
    component["purl"] = f"pkg:pypi/fastapi@{version}"
    component["bom-ref"] = component["purl"]
    return sbom


def test_advisory_review_blocks_exact_match_and_preserves_bounded_completeness() -> None:
    snapshot = load_advisory_snapshot("fixtures/security/advisory-snapshot-synthetic.json")
    review = build_security_review(_synthetic_sbom("0.999.0-test"), [snapshot])
    assert review["completeness"] == "complete"
    assert review["release_eligible"] is False
    assert review["blocking_findings"][0]["advisory_id"] == "TEST-2026-0001"
    assert review["blocking_findings"][0]["exact_version_affected"] is True

    bounded = load_advisory_snapshot("fixtures/security/advisory-snapshot-bounded.json")
    bounded_review = build_security_review(_synthetic_sbom("0.998.0-test"), [bounded])
    assert bounded_review["blocking_findings"] == []
    assert bounded_review["completeness"] == "bounded_or_unknown"
    assert bounded_review["release_eligible"] is False


def test_vex_requires_exact_observation_subject_evidence_approver_and_expiry() -> None:
    snapshot = load_advisory_snapshot("fixtures/security/advisory-snapshot-synthetic.json")
    sbom = _synthetic_sbom("0.999.0-test")
    purl = next(item["purl"] for item in sbom["components"] if item["name"].lower() == "fastapi")
    now = datetime.now(timezone.utc)
    subject_digest = build_security_review(sbom, [snapshot], now=now)["subject_digest"]
    vex = VexDecision(
        advisory_observation_id="OBS-TEST-FASTAPI-1",
        advisory_id="TEST-2026-0001",
        subject_digest=subject_digest,
        component_purl=purl,
        status="not_affected",
        justification="synthetic feature predicate is unreachable in this test subject",
        predicate="feature synthetic_test_path is absent",
        evidence=("tests/test_provenance_and_advisories.py",),
        approver="test-security-reviewer",
        policy_version="test-vex-policy-v1",
        issued_at=now,
        expires_at=now + timedelta(days=1),
        invalidation_triggers=("component_version_change", "feature_enablement_change"),
    )
    review = build_security_review(sbom, [snapshot], vex_decisions=[vex], now=now)
    assert review["blocking_findings"] == []
    assert review["release_eligible"] is True
    expired = build_security_review(sbom, [snapshot], vex_decisions=[vex], now=now + timedelta(days=2))
    assert expired["blocking_findings"]
    assert expired["matches"][0]["vex_status"] == "expired"


def test_security_review_verifier_binds_sbom_subject(tmp_path: Path) -> None:
    sbom = _synthetic_sbom("0.998.0-test")
    bounded = load_advisory_snapshot("fixtures/security/advisory-snapshot-bounded.json")
    review = build_security_review(sbom, [bounded])
    sbom_path = tmp_path / "sbom.json"
    review_path = tmp_path / "review.json"
    sbom_path.write_text(json.dumps(sbom))
    review_path.write_text(json.dumps(review))
    assert verify_security_review(review_path, sbom_path)["valid"] is True
    sbom["components"][0]["version"] = "changed"
    sbom_path.write_text(json.dumps(sbom))
    assert verify_security_review(review_path, sbom_path)["valid"] is False
