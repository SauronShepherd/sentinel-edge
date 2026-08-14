from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import uuid4
from typing import Any

import pytest

from sentinel_edge.domain.models import (
    AnalysisResult,
    ClaimEvidenceLink,
    ClaimEvidenceRelation,
    ClaimNode,
    CoverageState,
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
from sentinel_edge.storage import IncidentJournalStore


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def fixture() -> tuple[IncidentEventEngine, EvidenceTrustService]:
    store = IncidentJournalStore()
    incidents = IncidentEventEngine(store)
    incident = incidents.apply_analysis(
        AnalysisResult(
            observation_id=uuid4(),
            hazard=HazardKind.WILDFIRE,
            score=0.8,
            state_hint=IncidentState.SUSPECTED,
            features={},
            coverage=CoverageState.SUFFICIENT,
        )
    )
    assert incident.hazard is HazardKind.WILDFIRE
    return incidents, EvidenceTrustService(store)


def item(incident_id: Any, *, source: str, content: str, origin: str, independent: bool = False) -> EvidenceItem:
    return EvidenceItem(
        incident_id=incident_id,
        hazard=HazardKind.WILDFIRE,
        source_id=source,
        source_standing=SourceStanding.NEWS,
        media_integrity=MediaIntegrityState.DERIVATIVE,
        extraction_confidence_state=ExtractionConfidenceState.MODEL_ESTIMATE,
        extraction_confidence=0.82,
        freshness_state=HealthState.HEALTHY,
        claim_text="Visible smoke near the ridge",
        content_sha256=digest(content),
        perceptual_hash="phash-shared" if content != "independent" else "phash-independent",
        origin_key=origin,
        independent_origin_proven=independent,
        retention_state=EvidenceRetentionState.METADATA_ONLY,
        parser_state=ParserIsolationState.SANDBOXED,
        modality="image",
    )


def test_reposts_collapse_to_one_family_and_independence_requires_proof() -> None:
    incidents, service = fixture()
    incident = incidents.current()[0]
    first = service.ingest(item(incident.incident_id, source="publisher-a", content="same", origin="original-post-1"))
    second = service.ingest(item(incident.incident_id, source="publisher-b", content="same", origin="repost-2"))
    third = service.ingest(item(incident.incident_id, source="publisher-c", content="independent", origin="original-post-1", independent=True))

    assert first.family_id == second.family_id == third.family_id
    family = service.families(incident.incident_id)[0]
    assert len(family.evidence_ids) == 3
    assert family.exact_duplicates == 1
    assert family.independence_units == 2
    assert family.independent_origins == 1


def test_claim_graph_preserves_support_and_contradiction_separately() -> None:
    incidents, service = fixture()
    incident = incidents.current()[0]
    supporting = service.ingest(item(incident.incident_id, source="publisher-a", content="support", origin="origin-a"))
    contradicting = service.ingest(item(incident.incident_id, source="publisher-b", content="contradict", origin="origin-b", independent=True))
    claim = service.create_claim(ClaimNode(
        incident_id=incident.incident_id,
        hazard=HazardKind.WILDFIRE,
        statement="A wildfire is active near the ridge",
    ))
    service.link(ClaimEvidenceLink(claim_id=claim.claim_id, evidence_id=supporting.evidence_id, relation=ClaimEvidenceRelation.SUPPORTS))
    service.link(ClaimEvidenceLink(claim_id=claim.claim_id, evidence_id=contradicting.evidence_id, relation=ClaimEvidenceRelation.CONTRADICTS))

    snapshot = service.trust_snapshot(incident.incident_id)
    assert snapshot.supporting_links == 1
    assert snapshot.contradictory_links == 1
    assert snapshot.summary_band == "contested"
    assert snapshot.source_standing_counts == {"news": 2}
    assert snapshot.media_integrity_counts == {"derivative": 2}
    assert snapshot.extraction_confidence_counts == {"model_estimate": 2}
    assert "unresolved_contradictions_present" in snapshot.reason_codes
    assert service.graph_digest(incident.incident_id)


def test_external_media_requires_rights_for_retention_and_forbids_person_identification() -> None:
    incidents, _ = fixture()
    incident = incidents.current()[0]
    base = dict(
        incident_id=incident.incident_id,
        hazard=HazardKind.WILDFIRE,
        source_id="community",
        source_standing=SourceStanding.COMMUNITY,
        media_integrity=MediaIntegrityState.UNKNOWN,
        extraction_confidence_state=ExtractionConfidenceState.UNKNOWN,
        extraction_confidence=None,
        freshness_state=HealthState.UNKNOWN,
        claim_text="Unverified image",
        content_sha256=digest("media"),
        origin_key="community-post",
        retention_state=EvidenceRetentionState.RETAINED,
        parser_state=ParserIsolationState.SANDBOXED,
        modality="image",
    )
    with pytest.raises(ValueError, match="rights_basis"):
        EvidenceItem(**base)
    with pytest.raises(ValueError, match="person re-identification"):
        EvidenceItem(**{**base, "rights_basis": "consent-v1", "person_identification_performed": True})


def test_ten_reposts_are_one_family_until_independence_is_proven() -> None:
    incidents, service = fixture()
    incident = incidents.current()[0]
    for index in range(10):
        service.ingest(item(
            incident.incident_id,
            source=f"reposter-{index}",
            content="same-origin-content",
            origin=f"repost-url-{index}",
        ))
    families = service.families(incident.incident_id)
    assert len(families) == 1
    assert families[0].independence_units == 1
    assert families[0].exact_duplicates == 9


def test_low_trust_evidence_cannot_mutate_incident_state() -> None:
    incidents, service = fixture()
    before = incidents.current()[0]
    low_trust = EvidenceItem(
        incident_id=before.incident_id,
        hazard=HazardKind.WILDFIRE,
        source_id="anonymous-social",
        source_standing=SourceStanding.UNKNOWN,
        media_integrity=MediaIntegrityState.UNKNOWN,
        extraction_confidence_state=ExtractionConfidenceState.LOW,
        extraction_confidence=0.2,
        freshness_state=HealthState.UNKNOWN,
        claim_text="Anonymous report says the fire is extinguished",
        content_sha256=digest("anonymous-report"),
        origin_key="anonymous-post",
        retention_state=EvidenceRetentionState.METADATA_ONLY,
        parser_state=ParserIsolationState.SANDBOXED,
        modality="text",
    )
    service.ingest(low_trust)
    after = incidents.current()[0]
    assert after == before
    snapshot = service.trust_snapshot(before.incident_id)
    assert snapshot.source_standing_counts == {"unknown": 1}
    assert snapshot.summary_band == "unlinked_evidence"


def test_evidence_graph_reconciles_after_store_restart(tmp_path) -> None:
    path = tmp_path / "incidents.sqlite3"
    store = IncidentJournalStore(path)
    incidents = IncidentEventEngine(store)
    record = incidents.apply_analysis(AnalysisResult(
        observation_id=uuid4(), hazard=HazardKind.WILDFIRE, score=0.7,
        state_hint=IncidentState.SUSPECTED, features={}, coverage=CoverageState.SUFFICIENT,
    ))
    service = EvidenceTrustService(store)
    evidence = service.ingest(item(record.incident_id, source="local", content="restart", origin="local-frame"))
    claim = service.create_claim(ClaimNode(incident_id=record.incident_id, hazard=HazardKind.WILDFIRE, statement="Smoke observed"))
    service.link(ClaimEvidenceLink(claim_id=claim.claim_id, evidence_id=evidence.evidence_id, relation=ClaimEvidenceRelation.SUPPORTS))
    digest_before = service.graph_digest(record.incident_id)

    reopened_store = IncidentJournalStore(path)
    reopened = EvidenceTrustService(reopened_store)
    assert reopened.graph_digest(record.incident_id) == digest_before
    assert len(reopened_store.evidence(str(record.incident_id))) == 1
    assert len(reopened_store.claims(str(record.incident_id))) == 1
    assert len(reopened_store.claim_links(str(record.incident_id))) == 1
