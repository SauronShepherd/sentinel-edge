import json
import shutil
import socket
from pathlib import Path

from sentinel_edge.release import verify_release_candidate, write_release_candidate
from sentinel_edge.scenario import DeterministicScenarioEngine


def test_release_candidate_identity_is_stable_and_truthfully_not_admitted(tmp_path: Path) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    first = write_release_candidate(
        ".",
        version="0.3.0",
        configuration_state=engine.configuration.state(),
        capabilities=[item.model_dump(mode="json") for item in engine.capabilities.records()],
        output=tmp_path / "candidate-a.json",
    )
    second = write_release_candidate(
        ".",
        version="0.3.0",
        configuration_state=engine.configuration.state(),
        capabilities=[item.model_dump(mode="json") for item in engine.capabilities.records()],
        output=tmp_path / "candidate-b.json",
    )
    a = json.loads(first.read_text(encoding="utf-8"))
    b = json.loads(second.read_text(encoding="utf-8"))
    assert a["candidate_id"] == b["candidate_id"]
    assert a["identity"]["requirements"]["total"] == 743
    assert a["release_admitted"] is False
    assert verify_release_candidate(first, ".")["valid"] is True


def test_release_candidate_separates_frozen_artifacts_from_observed_environment(tmp_path: Path) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state-separation")
    candidate = write_release_candidate(
        ".", version="0.3.0", configuration_state=engine.configuration.state(),
        capabilities=[item.model_dump(mode="json") for item in engine.capabilities.records()],
        output=tmp_path / "candidate-separation.json",
    )
    identity = json.loads(candidate.read_text(encoding="utf-8"))["identity"]
    assert identity["frozen_entrant_artifacts"]["repository_inventory_digest"] == identity["inventory_digest"]
    assert identity["observed_environment"]["host_trust_report_sha256"] == identity["supply_chain"]["host_trust_report_sha256"]
    assert "host_trust_report_sha256" not in identity["frozen_entrant_artifacts"]


def test_release_candidate_verification_is_machine_readable_and_network_independent(tmp_path: Path, monkeypatch) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "offline-state")
    candidate = write_release_candidate(
        ".", version="0.3.0", configuration_state=engine.configuration.state(),
        capabilities=[item.model_dump(mode="json") for item in engine.capabilities.records()],
        output=tmp_path / "candidate-offline.json",
    )
    copied = tmp_path / "clean-clone"
    shutil.copytree(".", copied, ignore=shutil.ignore_patterns(".git", ".venv", ".pytest_cache", "__pycache__", "*.pyc", "release-candidate.json", "release-manifest.json"))
    def fail_network(*_args, **_kwargs):
        raise AssertionError("network access is forbidden during candidate verification")
    monkeypatch.setattr(socket, "create_connection", fail_network)
    result = verify_release_candidate(candidate, copied)
    assert isinstance(result, dict)
    assert {"valid", "candidate_id", "failures"}.issubset(result)


def test_release_candidate_binds_active_contract_generator_and_digest(tmp_path: Path) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "contract-state")
    candidate = write_release_candidate(
        ".", version="0.3.0", configuration_state=engine.configuration.state(),
        capabilities=[item.model_dump(mode="json") for item in engine.capabilities.records()],
        output=tmp_path / "candidate-contract.json",
    )
    identity = json.loads(candidate.read_text(encoding="utf-8"))["identity"]
    binding = identity["active_contract"]
    assert binding["generator_version"] == "generate_active_contract_snapshot.py@1"
    assert len(binding["digest"]) == 64
    assert any(item["path"] == "registries/requirements.yaml" for item in binding["inputs"])


def test_release_candidate_records_repository_state_and_dirty_admission_guard(tmp_path: Path) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "repo-state")
    candidate = write_release_candidate(
        ".", version="0.3.0", configuration_state=engine.configuration.state(),
        capabilities=[item.model_dump(mode="json") for item in engine.capabilities.records()],
        output=tmp_path / "candidate-repo-state.json",
    )
    payload = json.loads(candidate.read_text(encoding="utf-8"))
    assert "repository_state" in payload["identity"]
    assert payload["release_admitted"] is False


def test_release_candidate_reports_claim_artifact_scope(tmp_path: Path) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "claim-scope")
    candidate = write_release_candidate(
        ".", version="0.3.0", configuration_state=engine.configuration.state(),
        capabilities=[item.model_dump(mode="json") for item in engine.capabilities.records()],
        output=tmp_path / "candidate-claim-scope.json",
    )
    payload = json.loads(candidate.read_text(encoding="utf-8"))
    assert payload["identity"]["claim_artifact_scope"]["candidate_bound"] is True


def test_release_candidate_detects_repository_tampering(tmp_path: Path) -> None:
    copied = tmp_path / "repository"
    shutil.copytree(
        ".",
        copied,
        ignore=shutil.ignore_patterns(".git", ".venv", ".uv-cache", ".tmp", ".idea", "artifacts", "build", "dist", "node_modules", ".pytest_cache", "__pycache__", "*.pyc"),
    )
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    candidate = write_release_candidate(
        copied,
        version="0.3.0",
        configuration_state=engine.configuration.state(),
        capabilities=[item.model_dump(mode="json") for item in engine.capabilities.records()],
    )
    (copied / "README.md").write_text("tampered\n", encoding="utf-8")
    result = verify_release_candidate(candidate, copied)
    assert result["valid"] is False
    assert "inventory_digest_mismatch" in result["failures"]


def test_candidate_reopens_when_bound_security_review_changes(tmp_path: Path) -> None:
    from sentinel_edge.release import (
        write_cyclonedx_sbom,
        write_provenance,
        write_security_review,
    )

    copied = tmp_path / "repository-security"
    shutil.copytree(
        ".",
        copied,
        ignore=shutil.ignore_patterns(".git", ".venv", ".uv-cache", ".tmp", ".idea", "artifacts", "build", "dist", "node_modules", ".pytest_cache", "__pycache__", "*.pyc", "release-candidate.json", "release-manifest.json", "release-candidate.json.sig.json"),
    )
    write_cyclonedx_sbom(copied)
    snapshot = copied / "fixtures/security/advisory-snapshot-bounded.json"
    write_security_review(copied, [snapshot])
    write_provenance(copied)
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "security-state")
    candidate = write_release_candidate(
        copied,
        version="0.6.0",
        configuration_state=engine.configuration.state(),
        capabilities=[item.model_dump(mode="json") for item in engine.capabilities.records()],
    )
    before = verify_release_candidate(candidate, copied)
    assert before["valid"] is True
    review = copied / "security-review.json"
    payload = json.loads(review.read_text(encoding="utf-8"))
    payload["source_states"].append({"source": "new-observation", "completeness": "unknown"})
    review.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    after = verify_release_candidate(candidate, copied)
    assert after["valid"] is False
    assert "inventory_digest_mismatch" in after["failures"]


def test_release_candidate_binds_verified_privacy_closure(tmp_path: Path) -> None:
    from sentinel_edge.privacy import write_privacy_closure

    copied = tmp_path / "repository-privacy"
    shutil.copytree(
        ".",
        copied,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", ".uv-cache", ".tmp", ".idea", "artifacts", "build", "dist", "node_modules", ".pytest_cache", "__pycache__", "*.pyc",
            "release-candidate.json", "release-manifest.json", "release-candidate.json.sig.json",
            "build-provenance.json", "privacy-closure.json",
        ),
    )
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "privacy-state")
    write_privacy_closure(engine, repository_root=copied, output=copied / "privacy-closure.json")
    candidate = write_release_candidate(
        copied,
        version="0.14.0",
        configuration_state=engine.configuration.state(),
        capabilities=[item.model_dump(mode="json") for item in engine.capabilities.records()],
    )
    payload = json.loads(candidate.read_text(encoding="utf-8"))
    assert payload["identity"]["privacy"]["verified"] is True
    assert payload["identity"]["privacy"]["privacy_state_complete"] is True
    assert payload["release_admitted"] is False


def test_candidate_rejects_g0_gate_projection_mutation(tmp_path: Path) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "g0-state")
    candidate = write_release_candidate(
        ".",
        version="0.22.0",
        configuration_state=engine.configuration.state(),
        capabilities=[item.model_dump(mode="json") for item in engine.capabilities.records()],
        output=tmp_path / "candidate-g0.json",
    )
    g0_path = Path("qualification/g0-gate-status.json")
    original = g0_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        payload["packs"][0]["status"] = "fail"
        g0_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        result = verify_release_candidate(candidate, ".")
        assert result["valid"] is False
        assert "g0_gate_status_binding_mismatch" in result["failures"]
    finally:
        g0_path.write_text(original, encoding="utf-8", newline="\n")


def test_candidate_rejects_claim_registry_binding_mutation(tmp_path: Path) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "claim-state")
    candidate = write_release_candidate(
        ".", version="0.22.0", configuration_state=engine.configuration.state(),
        capabilities=[item.model_dump(mode="json") for item in engine.capabilities.records()],
        output=tmp_path / "candidate-claims.json",
    )
    claim_path = Path("qualification/claim-registry.json")
    original = claim_path.read_text(encoding="utf-8")
    try:
        claim_path.write_text(original + "\n", encoding="utf-8")
        result = verify_release_candidate(candidate, ".")
        assert result["valid"] is False
        assert "claim_registry_binding_mismatch" in result["failures"]
    finally:
        claim_path.write_text(original, encoding="utf-8", newline="\n")


def test_candidate_marks_invalid_claim_registry_not_valid(tmp_path: Path) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "invalid-claim-state")
    claim_path = Path("qualification/claim-registry.json")
    original = claim_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        payload["claims"][0]["artifact_refs"] = ["sha256:" + "0" * 64]
        claim_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        candidate = write_release_candidate(
            ".", version="0.22.0", configuration_state=engine.configuration.state(),
            capabilities=[item.model_dump(mode="json") for item in engine.capabilities.records()],
            output=tmp_path / "candidate-invalid-claims.json",
        )
        built = json.loads(candidate.read_text(encoding="utf-8"))
        assert built["identity"]["claim_registry"]["valid"] is False
    finally:
        claim_path.write_text(original, encoding="utf-8", newline="\n")


def test_candidate_rejects_claim_payload_different_from_registry(tmp_path: Path) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "claim-payload-state")
    try:
        write_release_candidate(
            ".", version="0.22.0", configuration_state=engine.configuration.state(),
            capabilities=[item.model_dump(mode="json") for item in engine.capabilities.records()],
            claims=[{"claim_id": "forged"}], output=tmp_path / "candidate-forged-claims.json",
        )
    except ValueError as exc:
        assert "must match the validated Claim Registry" in str(exc)
    else:
        raise AssertionError("divergent candidate claims were accepted")


def test_candidate_verification_rejects_bound_invalid_claim_registry(tmp_path: Path) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "invalid-claim-verify-state")
    claim_path = Path("qualification/claim-registry.json")
    original = claim_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        payload["claims"][0]["artifact_refs"] = ["sha256:" + "0" * 64]
        claim_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        candidate = write_release_candidate(
            ".", version="0.22.0", configuration_state=engine.configuration.state(),
            capabilities=[item.model_dump(mode="json") for item in engine.capabilities.records()],
            output=tmp_path / "candidate-invalid-claim-verify.json",
        )
        result = verify_release_candidate(candidate, ".")
        assert result["valid"] is False
        assert "claim_registry_invalid" in result["failures"]
    finally:
        claim_path.write_text(original, encoding="utf-8", newline="\n")
