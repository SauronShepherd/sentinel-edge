from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from pathlib import Path

import pytest

from sentinel_edge.domain.models import (
    AnalysisResult,
    ClaimEvidenceLink,
    ClaimEvidenceRelation,
    ClaimNode,
    CoverageState,
    EvidenceContentState,
    EvidenceItem,
    EvidenceRetentionState,
    ExtractionConfidenceState,
    HazardKind,
    HealthState,
    IncidentState,
    MediaIntegrityState,
    ParserIsolationState,
    SourceStanding,
)
from sentinel_edge.evidence import EvidenceTrustService
from sentinel_edge.incidents import IncidentEventEngine
from sentinel_edge.storage import ArtifactPolicy, ContentAddressedArtifactStore, IncidentJournalStore


def seeded(tmp_path: Path) -> tuple[object, object, object, EvidenceTrustService]:
    store = IncidentJournalStore(tmp_path / "incidents.sqlite3")
    incidents = IncidentEventEngine(store)
    incident = incidents.apply_analysis(AnalysisResult(
        observation_id=uuid4(), hazard=HazardKind.WILDFIRE, score=0.8,
        state_hint=IncidentState.SUSPECTED, features={}, coverage=CoverageState.SUFFICIENT,
    ))
    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts", max_bytes=1024 * 1024, reserve_bytes=1024)
    return incident, store, artifacts, EvidenceTrustService(store, artifacts)


def retained_item(incident_id: object, digest: str, *, received_at: datetime, expires_at: datetime | None = None) -> EvidenceItem:
    return EvidenceItem(
        incident_id=incident_id,
        hazard=HazardKind.WILDFIRE,
        source_id="camera-1",
        source_standing=SourceStanding.FIRST_PARTY,
        media_integrity=MediaIntegrityState.ORIGINAL_VERIFIED,
        extraction_confidence_state=ExtractionConfidenceState.VERIFIED,
        extraction_confidence=1.0,
        freshness_state=HealthState.HEALTHY,
        claim_text="Smoke visible",
        content_sha256=digest,
        origin_key="frame-1",
        retention_state=EvidenceRetentionState.RETAINED,
        parser_state=ParserIsolationState.SANDBOXED,
        rights_basis="device-owner",
        rights_expires_at=expires_at,
        modality="image",
        received_at=received_at,
    )


def test_deletion_removes_artifact_but_preserves_history_and_invalidates_claim(tmp_path) -> None:
    incident, store, artifacts, service = seeded(tmp_path)
    raw = b"retained-media-content"
    ref = artifacts.put_bytes(raw, media_type="image/png", policy=ArtifactPolicy.incident_evidence())
    evidence = service.ingest(retained_item(incident.incident_id, ref.sha256, received_at=datetime.now(timezone.utc)))
    claim = service.create_claim(ClaimNode(
        incident_id=incident.incident_id, hazard=HazardKind.WILDFIRE, statement="Wildfire evidence exists"
    ))
    service.link(ClaimEvidenceLink(
        claim_id=claim.claim_id, evidence_id=evidence.evidence_id, relation=ClaimEvidenceRelation.SUPPORTS
    ))
    assert service.trust_snapshot(incident.incident_id).supporting_links == 1

    redacted = service.transition(
        evidence.evidence_id, to_state=EvidenceContentState.REDACTED, expected_version=1,
        actor="privacy-admin", reason="minimize public display", redaction_profile_id="metadata-only-v1",
    )
    assert redacted.state is EvidenceContentState.REDACTED
    assert redacted.readable is False
    assert redacted.claim_eligible is True

    deleted = service.transition(
        evidence.evidence_id, to_state=EvidenceContentState.DELETED, expected_version=2,
        actor="privacy-admin", reason="approved erasure",
    )
    assert deleted.state is EvidenceContentState.DELETED
    assert deleted.deletion_proven is True
    assert artifacts.verify(ref) is False
    reconciliation = service.claim_reconciliation(incident.incident_id)
    assert reconciliation == {
        "incident_id": str(incident.incident_id),
        "active_supporting_links": 0,
        "active_contradictory_links": 0,
        "invalidated_links": 1,
        "historical_link_count": 1,
        "history_rewritten": False,
    }
    assert len(store.claim_links(str(incident.incident_id))) == 1
    reevaluations = store.evidence_reevaluations(str(incident.incident_id))
    assert len(reevaluations) == 1
    assert reevaluations[0].invalidated_links == 1
    assert reevaluations[0].incident_state_mutated is False
    with pytest.raises(ValueError, match="illegal evidence lifecycle transition"):
        service.transition(
            evidence.evidence_id, to_state=EvidenceContentState.REDACTED, expected_version=3,
            actor="privacy-admin", reason="attempt restore",
        )


def test_rights_expiry_is_idempotent_and_restart_reconstructs_projection(tmp_path) -> None:
    incident, store, artifacts, service = seeded(tmp_path)
    received = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
    expires = received + timedelta(hours=1)
    ref = artifacts.put_bytes(b"expiring-content", policy=ArtifactPolicy.incident_evidence())
    evidence = service.ingest(retained_item(incident.incident_id, ref.sha256, received_at=received, expires_at=expires))
    assert service.enforce_rights_expiry(now=expires - timedelta(seconds=1)) == ()
    first = service.enforce_rights_expiry(now=expires + timedelta(seconds=1))
    assert len(first) == 1
    assert first[0].state is EvidenceContentState.EXPIRED
    assert first[0].claim_eligible is False
    assert service.enforce_rights_expiry(now=expires + timedelta(hours=1)) == ()

    reopened = EvidenceTrustService(IncidentJournalStore(tmp_path / "incidents.sqlite3"), artifacts)
    projection = reopened.lifecycle(evidence.evidence_id)
    assert projection.state is EvidenceContentState.EXPIRED
    assert projection.version == 2
    assert len(reopened.store.evidence_lifecycle_events(evidence_id=str(evidence.evidence_id))) == 2


def test_stale_lifecycle_version_and_premature_expiry_fail_closed(tmp_path) -> None:
    incident, _, artifacts, service = seeded(tmp_path)
    now = datetime.now(timezone.utc)
    ref = artifacts.put_bytes(b"future-rights", policy=ArtifactPolicy.incident_evidence())
    evidence = service.ingest(retained_item(
        incident.incident_id, ref.sha256, received_at=now, expires_at=now + timedelta(days=1)
    ))
    with pytest.raises(ValueError, match="rights have not expired"):
        service.transition(
            evidence.evidence_id, to_state=EvidenceContentState.EXPIRED, expected_version=1,
            actor="system", reason="premature", now=now,
        )
    service.transition(
        evidence.evidence_id, to_state=EvidenceContentState.REDACTED, expected_version=1,
        actor="admin", reason="redact", redaction_profile_id="metadata-v1",
    )
    with pytest.raises(ValueError, match="stale version"):
        service.transition(
            evidence.evidence_id, to_state=EvidenceContentState.DELETED, expected_version=1,
            actor="admin", reason="stale delete",
        )
