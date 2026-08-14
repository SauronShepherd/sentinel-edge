from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from sentinel_edge.storage import ArtifactPolicy

from sentinel_edge.domain.models import (
    EvidenceItem,
    EvidenceRetentionState,
    ExtractionConfidenceState,
    HazardKind,
    HealthState,
    MediaIntegrityState,
    ParserIsolationState,
    SourceStanding,
)
from sentinel_edge.privacy import DispositionAction, DispositionNodeKind
from sentinel_edge.scenario import DeterministicScenarioEngine, load_scenario
from sentinel_edge.security import SecretReference, SecretRegistry, SecretRotationPlan, SecretState


def seed(tmp_path: Path) -> Any:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    engine.run(load_scenario("fixtures/scenarios/simultaneous-event.json"))
    incident = next(item for item in engine.incidents.current() if item.hazard is HazardKind.WILDFIRE)
    ref = engine.artifacts.put_bytes(b"subject-content", media_type="image/png", policy=ArtifactPolicy.incident_evidence())
    evidence = engine.evidence.ingest(EvidenceItem(
        incident_id=incident.incident_id,
        hazard=HazardKind.WILDFIRE,
        source_id="camera-subject",
        source_standing=SourceStanding.FIRST_PARTY,
        media_integrity=MediaIntegrityState.ORIGINAL_VERIFIED,
        extraction_confidence_state=ExtractionConfidenceState.VERIFIED,
        extraction_confidence=1.0,
        freshness_state=HealthState.HEALTHY,
        claim_text="Subject-linked retained frame",
        content_sha256=ref.sha256,
        origin_key="subject-frame",
        retention_state=EvidenceRetentionState.RETAINED,
        parser_state=ParserIsolationState.SANDBOXED,
        rights_basis="device-owner",
        modality="image",
    ))
    return engine, evidence, ref


def test_disposition_reports_external_pending_then_closes_and_preserves_minimal_tombstone(tmp_path: Path) -> None:
    engine, evidence, ref = seed(tmp_path)
    local = engine.disposition.register_node(
        evidence_id=evidence.evidence_id,
        kind=DispositionNodeKind.THUMBNAIL,
        target_ref=f"artifact-sha256:{ref.sha256}",
    )
    external = engine.disposition.register_node(
        evidence_id=evidence.evidence_id,
        kind=DispositionNodeKind.EXTERNAL_RECIPIENT,
        target_ref="recipient-copy:case-1",
        external_recipient="processor@example.invalid",
    )
    created = datetime(2026, 8, 3, 1, 0, tzinfo=timezone.utc)
    request = engine.disposition.create_request(
        action=DispositionAction.ERASE,
        evidence_ids=(evidence.evidence_id,),
        subject_ref="subject@example.invalid",
        subject_basis="consent",
        actor="privacy-admin",
        reason="approved erasure",
        deadline=created + timedelta(days=7),
        created_at=created,
    )
    assert engine.disposition.is_restricted(evidence.evidence_id)
    report = engine.disposition.close(request.request_id, evidence_service=engine.evidence, artifact_store=engine.artifacts, now=created + timedelta(hours=1))
    assert report.external_recipient_pending == 1
    assert report.status.value == "external_recipient_pending"
    engine.disposition.acknowledge_external_recipient(
        external.node_id, actor="processor-contact", receipt="deleted from processor store", created_at=created + timedelta(hours=2)
    )
    report2 = engine.disposition.close(request.request_id, evidence_service=engine.evidence, artifact_store=engine.artifacts, now=created + timedelta(hours=3))
    assert report2.external_recipient_pending == 0
    assert report2.status.value == "completed"
    tombstone = engine.disposition.minimal_tombstone(request.request_id)
    assert tombstone["content_retained"] is False
    assert tombstone["exact_location_retained"] is False
    assert "subject@example.invalid" not in str(tombstone)
    assert local.node_id != external.node_id


def test_consent_withdrawal_blocks_future_consent_processing_until_alternate_basis(tmp_path: Path) -> None:
    engine, evidence, _ = seed(tmp_path)
    now = datetime(2026, 8, 3, tzinfo=timezone.utc)
    engine.disposition.create_request(
        action=DispositionAction.CONSENT_WITHDRAWAL,
        evidence_ids=(evidence.evidence_id,),
        subject_ref="subject-42",
        subject_basis="consent",
        actor="privacy-admin",
        reason="withdrawn",
        deadline=now + timedelta(days=2),
        created_at=now,
    )
    denied = engine.disposition.processing_allowed(subject_ref="subject-42", basis="consent")
    assert denied["allowed"] is False
    assert engine.disposition.processing_allowed(subject_ref="subject-42", basis="vital_interest")["allowed"] is True
    engine.disposition.document_alternate_basis(
        "subject-42", basis="documented_non_consent_basis", actor="privacy-admin", reason="field safety retention"
    )
    assert engine.disposition.processing_allowed(subject_ref="subject-42", basis="consent")["allowed"] is True


def test_secret_registry_persists_only_metadata_and_enforces_scope_rotation_and_handle_expiry(tmp_path: Path) -> None:
    now = datetime(2026, 8, 3, tzinfo=timezone.utc)
    registry = SecretRegistry(tmp_path / "secret-metadata.sqlite3", maximum_handle_seconds=120)
    old = SecretReference(
        reference_id="meteoalarm-api",
        version=1,
        owner_module="collector",
        purpose="source-authentication",
        policy_version="secret-policy-v1",
        valid_from=now - timedelta(days=1),
        valid_until=now + timedelta(days=3),
        state=SecretState.ACTIVE,
    )
    new = old.model_copy(update={"version": 2, "state": SecretState.STAGED})
    secret_old = b"old-canary-secret-value"
    secret_new = b"new-canary-secret-value"
    registry.register(old, secret_old)
    registry.register(new, secret_new)
    raw_db = (tmp_path / "secret-metadata.sqlite3").read_bytes()
    assert secret_old not in raw_db and secret_new not in raw_db
    with pytest.raises(PermissionError, match="module or purpose"):
        registry.resolve(old.key, requesting_module="runtime", purpose="source-authentication", now=now)
    handle = registry.resolve(old.key, requesting_module="collector", purpose="source-authentication", now=now, lifetime_seconds=30)
    assert registry.read(handle, now=now + timedelta(seconds=5)) == secret_old
    plan = SecretRotationPlan(
        reference_id=old.reference_id,
        old_version=1,
        new_version=2,
        overlap_starts_at=now,
        cutover_at=now + timedelta(minutes=5),
        overlap_ends_at=now + timedelta(minutes=10),
        maximum_overlap_seconds=900,
    )
    plan_id = registry.plan_rotation(plan)
    registry.apply_rotation(plan_id, now=now + timedelta(minutes=11))
    with pytest.raises(PermissionError, match="stale or unknown"):
        registry.read(handle, now=now + timedelta(minutes=11))
    assert registry.capability_state(old.key, now=now + timedelta(minutes=11))["local_physical_monitoring_affected"] is False


def test_registered_lineage_closure_covers_local_indexes_grants_leases_and_external_copies(tmp_path: Path) -> None:
    engine, evidence, ref = seed(tmp_path)
    local_kinds = (
        DispositionNodeKind.ORIGINAL,
        DispositionNodeKind.REDACTION,
        DispositionNodeKind.THUMBNAIL,
        DispositionNodeKind.OCR,
        DispositionNodeKind.ASR,
        DispositionNodeKind.EMBEDDING,
        DispositionNodeKind.SEARCH_INDEX,
        DispositionNodeKind.CACHE,
    )
    for kind in local_kinds:
        target = f"artifact-sha256:{ref.sha256}" if kind is DispositionNodeKind.ORIGINAL else f"logical:{kind.value}:1"
        engine.disposition.register_node(evidence_id=evidence.evidence_id, kind=kind, target_ref=target)
    for kind in (DispositionNodeKind.GRANT, DispositionNodeKind.LEASE):
        engine.disposition.register_node(evidence_id=evidence.evidence_id, kind=kind, target_ref=f"logical:{kind.value}:1")
    external_nodes = [
        engine.disposition.register_node(
            evidence_id=evidence.evidence_id,
            kind=kind,
            target_ref=f"external:{kind.value}:1",
            external_recipient=f"{kind.value}@processor.invalid",
        )
        for kind in (DispositionNodeKind.EXPORT, DispositionNodeKind.REPLICA, DispositionNodeKind.EXTERNAL_RECIPIENT)
    ]
    now = datetime(2026, 8, 3, 2, 0, tzinfo=timezone.utc)
    request = engine.disposition.create_request(
        action=DispositionAction.ERASE,
        evidence_ids=(evidence.evidence_id,),
        subject_ref="subject-lineage",
        subject_basis="consent",
        actor="privacy-admin",
        reason="lineage closure",
        deadline=now + timedelta(days=3),
        created_at=now,
    )
    first = engine.disposition.close(request.request_id, evidence_service=engine.evidence, artifact_store=engine.artifacts, now=now)
    assert first.external_recipient_pending == 3
    for node in external_nodes:
        engine.disposition.acknowledge_external_recipient(
            node.node_id, actor="recipient", receipt="deleted", created_at=now + timedelta(minutes=1)
        )
    final = engine.disposition.close(
        request.request_id, evidence_service=engine.evidence, artifact_store=engine.artifacts, now=now + timedelta(minutes=2)
    )
    assert final.status.value == "completed"
    assert final.external_recipient_pending == 0
    assert final.failed == 0
    assert {item.kind for item in final.node_results} >= set(DispositionNodeKind)


def test_secret_canary_is_detected_in_logs_traces_errors_and_support_bundles(tmp_path: Path) -> None:
    registry = SecretRegistry(tmp_path / "metadata.sqlite3")
    secret = b"sentinel-canary-secret-should-never-leak"
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    for name in ("application.log", "trace.jsonl", "error.txt", "support-bundle.txt"):
        (outputs / name).write_bytes(b"prefix:" + secret + b":suffix")
    assert set(registry.scan_for_secret(outputs, secret)) == {
        "application.log", "error.txt", "support-bundle.txt", "trace.jsonl"
    }
    for path in outputs.iterdir():
        path.write_text("[REDACTED]\n", encoding="utf-8")
    assert registry.scan_for_secret(outputs, secret) == ()
