from __future__ import annotations

import json
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from sentinel_edge.storage.restore_authorization import RestoreAuthorization

from sentinel_edge.domain.models import (
    EvidenceContentState,
    EvidenceItem,
    EvidenceRetentionState,
    ExtractionConfidenceState,
    HazardKind,
    HealthState,
    MediaIntegrityState,
    ParserIsolationState,
    SourceStanding,
)
from sentinel_edge.evidence import EvidenceTrustService
from sentinel_edge.exports import (
    ArtifactClassification,
    DerivedArtifactSelection,
    EvidenceExportSelection,
    EvidenceExportService,
)
from sentinel_edge.privacy import write_tombstone_journal
from sentinel_edge.scenario import DeterministicScenarioEngine, load_scenario
from sentinel_edge.storage import ArtifactPolicy, ContentAddressedArtifactStore, IncidentJournalStore, StateBackupManager


def seed_retained_evidence(tmp_path: Path) -> Any:
    state = tmp_path / "state"
    engine = DeterministicScenarioEngine(state_dir=state)
    engine.run(load_scenario("fixtures/scenarios/simultaneous-event.json"))
    incident = next(item for item in engine.incidents.current() if item.hazard is HazardKind.WILDFIRE)
    content = b"private-retained-evidence"
    ref = engine.artifacts.put_bytes(content, media_type="image/png", policy=ArtifactPolicy.incident_evidence())
    evidence = engine.evidence.ingest(EvidenceItem(
        incident_id=incident.incident_id,
        hazard=HazardKind.WILDFIRE,
        source_id="camera-private-1",
        source_standing=SourceStanding.FIRST_PARTY,
        media_integrity=MediaIntegrityState.ORIGINAL_VERIFIED,
        extraction_confidence_state=ExtractionConfidenceState.VERIFIED,
        extraction_confidence=1.0,
        freshness_state=HealthState.HEALTHY,
        claim_text="Private smoke observation at exact location",
        content_sha256=ref.sha256,
        origin_key="private-frame-1",
        retention_state=EvidenceRetentionState.RETAINED,
        parser_state=ParserIsolationState.SANDBOXED,
        rights_basis="device-owner",
        modality="image",
    ))
    return state, engine, incident, evidence, ref


def test_pre_deletion_backup_reapplies_newer_tombstone_before_readiness(tmp_path: Path) -> None:
    state, engine, _, evidence, _ = seed_retained_evidence(tmp_path)
    manager = StateBackupManager()
    backup = tmp_path / "pre-delete.zip"
    manager.create(state, backup, created_at=datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc))

    engine.evidence.transition(
        evidence.evidence_id,
        to_state=EvidenceContentState.DELETED,
        expected_version=1,
        actor="privacy-admin",
        reason="approved erasure",
    )
    current_journal = tmp_path / "current-tombstones.json"
    journal = write_tombstone_journal(engine.evidence.store, current_journal)
    assert journal.lifecycle_event_count == 1

    restored = tmp_path / "restored"
    result = manager.restore(backup, restored, current_tombstone_journal=current_journal,
        authorization=RestoreAuthorization(actor="operator", reason="privacy recovery", target_node="local-node", target_namespace="restored", policy_version="restore-v1"))
    assert result["tombstones_applied_before_readiness"] is True
    assert result["current_tombstones"]["applied"] == 1

    restored_store = IncidentJournalStore(restored / "incidents.sqlite3")
    restored_service = EvidenceTrustService(
        restored_store,
        ContentAddressedArtifactStore(restored / "artifacts", max_bytes=1024 * 1024, reserve_bytes=1024),
    )
    projection = restored_service.lifecycle(evidence.evidence_id)
    assert projection.state is EvidenceContentState.DELETED
    assert projection.claim_eligible is False
    assert (restored / ".restore-reconciled.json").is_file()


def test_backup_privacy_manifest_and_exact_legal_hold_control_deletion(tmp_path: Path) -> None:
    state, _, _, _, _ = seed_retained_evidence(tmp_path)
    created = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
    backup = tmp_path / "held.zip"
    manager = StateBackupManager()
    manager.create(
        state,
        backup,
        retention_days=1,
        created_at=created,
        legal_hold_id="HOLD-001",
        legal_hold_reason="active investigation",
        legal_hold_expires_at=created + timedelta(days=3),
        legal_hold_review_due_at=created + timedelta(days=2),
    )
    verification = manager.verify(backup)
    assert verification["valid"] is True
    privacy = verification["privacy"]
    assert privacy["legal_hold"]["backup_id"] == verification["backup_id"]
    assert privacy["tombstone_journal_sha256"]

    held = manager.retention_decision(backup, now=created + timedelta(days=2))
    assert held["retention_expired"] is True
    assert held["active_legal_hold"] is True
    assert held["removable"] is False
    with pytest.raises(PermissionError, match="not removable"):
        manager.delete_if_expired(backup, now=created + timedelta(days=2), actor="backup-admin")

    receipt_path = tmp_path / "backup-delete-receipt.json"
    receipt = manager.delete_if_expired(
        backup,
        now=created + timedelta(days=4),
        actor="backup-admin",
        receipt_path=receipt_path,
    )
    assert receipt["backup_id"] == verification["backup_id"]
    assert not backup.exists()
    assert json.loads(receipt_path.read_text())["receipt_sha256"] == receipt["receipt_sha256"]


def test_backup_without_privacy_closure_is_rejected(tmp_path: Path) -> None:
    state, _, _, _, _ = seed_retained_evidence(tmp_path)
    manager = StateBackupManager()
    backup = tmp_path / "backup.zip"
    manager.create(state, backup)
    stripped = tmp_path / "stripped.zip"
    with zipfile.ZipFile(backup) as source, zipfile.ZipFile(stripped, "w") as target:
        for name in source.namelist():
            if name != "privacy-tombstones.json":
                target.writestr(name, source.read(name))
    result = manager.verify(stripped)
    assert result["valid"] is False
    assert "archive_member_closure_failed" in result["errors"] or "tombstone_journal_missing" in result["errors"]


def test_export_manifest_is_closed_rights_aware_and_redacts_restricted_metadata(tmp_path: Path) -> None:
    _, engine, _, evidence, ref = seed_retained_evidence(tmp_path)
    derived = engine.artifacts.put_bytes(b"thumbnail", media_type="image/png", policy=ArtifactPolicy.sanitized_media())
    service = EvidenceExportService(engine.evidence, engine.artifacts)
    output = tmp_path / "export.zip"
    manifest = service.create(
        output,
        selections=(EvidenceExportSelection(
            evidence_id=evidence.evidence_id,
            classification=ArtifactClassification.RESTRICTED,
            include_content=True,
            redaction_profile="restricted-export-v1",
        ),),
        derivatives=(DerivedArtifactSelection(
            source_evidence_id=evidence.evidence_id,
            artifact_sha256=derived.sha256,
            media_type="image/png",
            classification=ArtifactClassification.RESTRICTED,
            transformation="thumbnail-v1",
            redactions=("metadata_stripped",),
        ),),
        created_at=datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc),
    )
    assert manifest.secret_values_persisted is False
    assert service.verify(output)["valid"] is True
    derivative_members = [member for member in manifest.members if member.path.startswith("derivatives/")]
    assert len(derivative_members) == 1
    assert derivative_members[0].target_binding == f"artifact-sha256:{derived.sha256}"
    assert derivative_members[0].transformation == "thumbnail-v1"
    assert derivative_members[0].redactions == ("metadata_stripped",)
    with zipfile.ZipFile(output) as archive:
        metadata = json.loads(archive.read(f"evidence/{evidence.evidence_id}/metadata.json"))
        assert metadata["claim_text"] == "[REDACTED]"
        assert metadata["source_id"].startswith("source-sha256:")
        assert archive.read(f"evidence/{evidence.evidence_id}/content.bin") == b"private-retained-evidence"
        assert hashlib_sha256(archive.read(f"evidence/{evidence.evidence_id}/content.bin")) == ref.sha256


def hashlib_sha256(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


def test_export_rejects_secret_prohibited_derivative_downgrade_and_deleted_content(tmp_path: Path) -> None:
    _, engine, _, evidence, _ = seed_retained_evidence(tmp_path)
    service = EvidenceExportService(engine.evidence, engine.artifacts)
    with pytest.raises(ValueError, match="secret-prohibited"):
        service.create(
            tmp_path / "secret.zip",
            selections=(EvidenceExportSelection(
                evidence_id=evidence.evidence_id,
                classification=ArtifactClassification.SECRET_PROHIBITED,
            ),),
        )

    derivative = engine.artifacts.put_bytes(b"public-thumbnail", policy=ArtifactPolicy.release_proof())
    with pytest.raises(PermissionError, match="less restrictive"):
        service.create(
            tmp_path / "downgrade.zip",
            selections=(EvidenceExportSelection(
                evidence_id=evidence.evidence_id,
                classification=ArtifactClassification.RESTRICTED,
            ),),
            derivatives=(DerivedArtifactSelection(
                source_evidence_id=evidence.evidence_id,
                artifact_sha256=derivative.sha256,
                media_type="image/png",
                classification=ArtifactClassification.PUBLIC,
                transformation="thumbnail-v1",
            ),),
        )
    engine.evidence.transition(
        evidence.evidence_id,
        to_state=EvidenceContentState.DELETED,
        expected_version=1,
        actor="privacy-admin",
        reason="erase",
    )
    with pytest.raises(PermissionError, match="not exportable"):
        service.create(
            tmp_path / "deleted.zip",
            selections=(EvidenceExportSelection(
                evidence_id=evidence.evidence_id,
                classification=ArtifactClassification.RESTRICTED,
                include_content=True,
            ),),
        )


def test_export_authorization_denies_restricted_raw_media_without_govern_permission() -> None:
    from sentinel_edge.security import AuthManager, AuthorizationError
    from sentinel_edge.domain.models import PrincipalRef, PrincipalRole

    auth = AuthManager((("viewer-token-123456789", PrincipalRef(principal_id="viewer", roles=(PrincipalRole.VIEWER,))),))
    principal = auth.authenticate("viewer-token-123456789")
    with pytest.raises(AuthorizationError):
        auth.authorize(principal, "evidence:govern")


def test_export_verifier_rejects_undeclared_member(tmp_path: Path) -> None:
    _, engine, _, evidence, _ = seed_retained_evidence(tmp_path)
    service = EvidenceExportService(engine.evidence, engine.artifacts)
    output = tmp_path / "export.zip"
    service.create(
        output,
        selections=(EvidenceExportSelection(
            evidence_id=evidence.evidence_id,
            classification=ArtifactClassification.RESTRICTED,
        ),),
    )
    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(output) as source, zipfile.ZipFile(tampered, "w") as target:
        for name in source.namelist():
            target.writestr(name, source.read(name))
        target.writestr("undeclared.txt", b"not in manifest")
    result = service.verify(tampered)
    assert result["valid"] is False
    assert "member_closure_failed" in result["errors"]


def test_finalized_export_manifest_hash_detects_tampering(tmp_path: Path) -> None:
    _, engine, _, evidence, _ = seed_retained_evidence(tmp_path)
    service = EvidenceExportService(engine.evidence, engine.artifacts)
    output = tmp_path / "finalized.zip"
    service.create(
        output,
        selections=(EvidenceExportSelection(
            evidence_id=evidence.evidence_id,
            classification=ArtifactClassification.RESTRICTED,
        ),),
    )
    tampered = tmp_path / "tampered-manifest.zip"
    with zipfile.ZipFile(output) as source, zipfile.ZipFile(tampered, "w") as target:
        for name in source.namelist():
            data = source.read(name)
            if name == "manifest.json":
                manifest = json.loads(data)
                manifest["manifest_payload_sha256"] = "0" * 64
                data = json.dumps(manifest).encode("utf-8")
            target.writestr(name, data)
    result = service.verify(tampered)
    assert result["valid"] is False
    assert any(error.startswith("manifest_invalid:") for error in result["errors"])
