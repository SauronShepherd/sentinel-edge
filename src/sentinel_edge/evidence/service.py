from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, UUID, uuid5

from sentinel_edge.domain.models import (
    ClaimEvidenceLink,
    ClaimEvidenceRelation,
    ClaimNode,
    EvidenceContentState,
    EvidenceFamilySummary,
    EvidenceItem,
    EvidenceLifecycleAction,
    EvidenceLifecycleEvent,
    EvidenceLifecycleProjection,
    EvidenceReevaluationRecord,
    ExtractionConfidenceState,
    MediaIntegrityState,
    SourceStanding,
    TrustDimensionSnapshot,
)
from sentinel_edge.security import canonical_json_bytes, sha256_bytes
from sentinel_edge.storage import ArtifactPolicy, ArtifactScope, ContentAddressedArtifactStore, IncidentJournalStore


_LEGAL_TRANSITIONS: dict[EvidenceContentState, frozenset[EvidenceContentState]] = {
    EvidenceContentState.AVAILABLE: frozenset({
        EvidenceContentState.REDACTED,
        EvidenceContentState.EXPIRED,
        EvidenceContentState.DELETED,
        EvidenceContentState.MISSING_EXTERNAL,
    }),
    EvidenceContentState.METADATA_ONLY: frozenset({
        EvidenceContentState.EXPIRED,
        EvidenceContentState.DELETED,
        EvidenceContentState.MISSING_EXTERNAL,
    }),
    EvidenceContentState.REDACTED: frozenset({
        EvidenceContentState.EXPIRED,
        EvidenceContentState.DELETED,
        EvidenceContentState.MISSING_EXTERNAL,
    }),
    EvidenceContentState.EXPIRED: frozenset({EvidenceContentState.DELETED}),
    EvidenceContentState.MISSING_EXTERNAL: frozenset({EvidenceContentState.DELETED}),
    EvidenceContentState.UNAVAILABLE_AT_CAPTURE: frozenset({EvidenceContentState.DELETED}),
    EvidenceContentState.DELETED: frozenset(),
}

_ACTION_FOR_STATE = {
    EvidenceContentState.REDACTED: EvidenceLifecycleAction.REDACT,
    EvidenceContentState.EXPIRED: EvidenceLifecycleAction.EXPIRE,
    EvidenceContentState.DELETED: EvidenceLifecycleAction.DELETE,
    EvidenceContentState.MISSING_EXTERNAL: EvidenceLifecycleAction.MARK_EXTERNAL_MISSING,
}


class EvidenceTrustService:
    """Component-4 evidence/claim graph with explicit lifecycle and independence accounting."""

    def __init__(
        self,
        store: IncidentJournalStore,
        artifacts: ContentAddressedArtifactStore | None = None,
    ) -> None:
        self.store = store
        self.artifacts = artifacts
        self.disposition = None

    def set_disposition_service(self, disposition: Any) -> None:
        self.disposition = disposition

    @staticmethod
    def _family_seed(item: EvidenceItem) -> str:
        if item.parent_evidence_id is not None:
            return f"parent:{item.parent_evidence_id}"
        if item.perceptual_hash:
            return f"phash:{item.perceptual_hash}"
        if item.origin_key:
            return f"origin:{item.origin_key.strip().lower()}"
        return f"sha256:{item.content_sha256}"

    def _item(self, evidence_id: UUID) -> EvidenceItem:
        item = next((item for item in self.store.evidence() if item.evidence_id == evidence_id), None)
        if item is None:
            raise KeyError(str(evidence_id))
        return item

    def ingest(self, item: EvidenceItem) -> EvidenceItem:
        if self.disposition is not None and item.subject_ref is not None:
            decision = self.disposition.processing_allowed(subject_ref=item.subject_ref, basis=item.processing_basis)
            if not decision["allowed"]:
                raise ValueError("future processing blocked by consent withdrawal")
        current_incident = next(
            (record for record in self.store.latest_by_hazard() if record.incident_id == item.incident_id),
            None,
        )
        if current_incident is None or current_incident.hazard is not item.hazard:
            raise ValueError("evidence must target an existing incident with the same hazard")

        existing = self.store.evidence(str(item.incident_id))
        family_id: str | None = None
        for prior in existing:
            exact = prior.content_sha256 == item.content_sha256
            near = bool(prior.perceptual_hash and item.perceptual_hash and prior.perceptual_hash == item.perceptual_hash)
            same_origin = prior.origin_key.strip().lower() == item.origin_key.strip().lower()
            parent_match = item.parent_evidence_id == prior.evidence_id or prior.parent_evidence_id == item.evidence_id
            if exact or near or same_origin or parent_match:
                family_id = prior.family_id
                break
        if family_id is None:
            seed = self._family_seed(item)
            family_id = str(uuid5(NAMESPACE_URL, f"sentinel-evidence-family:{item.incident_id}:{seed}"))
        assigned = item.model_copy(update={"family_id": family_id})
        if self.artifacts is not None:
            artifact_path = self.artifacts.root / assigned.content_sha256[:2] / assigned.content_sha256[2:]
            if artifact_path.is_file():
                self.artifacts.catalog.register(
                    sha256=assigned.content_sha256,
                    relative_path=artifact_path.relative_to(self.artifacts.root).as_posix(),
                    bytes_count=artifact_path.stat().st_size,
                    media_type="application/octet-stream",
                    policy=ArtifactPolicy.incident_evidence(restricted=True),
                    scope=ArtifactScope(source_id=assigned.source_id, incident_id=str(assigned.incident_id)),
                    critical=True,
                )
        return self.store.record_evidence(assigned)

    def lifecycle(self, evidence_id: UUID) -> EvidenceLifecycleProjection:
        return self.store.evidence_lifecycle_projection(str(evidence_id))

    def lifecycle_events(self, incident_id: UUID) -> tuple[EvidenceLifecycleEvent, ...]:
        return self.store.evidence_lifecycle_events(incident_id=str(incident_id))

    def transition(
        self,
        evidence_id: UUID,
        *,
        to_state: EvidenceContentState,
        expected_version: int,
        actor: str,
        reason: str,
        now: datetime | None = None,
        redaction_profile_id: str | None = None,
    ) -> EvidenceLifecycleProjection:
        now = now or datetime.now(timezone.utc)
        item = self._item(evidence_id)
        current = self.lifecycle(evidence_id)
        if current.version != expected_version:
            raise ValueError("evidence lifecycle stale version")
        if to_state not in _LEGAL_TRANSITIONS[current.state]:
            raise ValueError(f"illegal evidence lifecycle transition: {current.state.value}->{to_state.value}")
        if to_state is EvidenceContentState.EXPIRED:
            if item.rights_expires_at is None or item.rights_expires_at > now:
                raise ValueError("evidence rights have not expired")
        deletion_proof = None
        reason_codes: list[str] = []
        if to_state is EvidenceContentState.DELETED:
            if self.artifacts is None:
                deletion_proof = sha256_bytes(
                    canonical_json_bytes({
                        "profile": "sentinel-evidence-delete-v1",
                        "artifact_sha256": item.content_sha256,
                        "artifact_store": "not_configured",
                    })
                )
                reason_codes.append("artifact_store_not_configured_metadata_deletion_only")
            else:
                result = self.artifacts.delete_digest(item.content_sha256, actor=actor, tombstone_authorized=True)
                deletion_proof = str(result["deletion_proof_sha256"])
                reason_codes.append("artifact_removed" if result["existed"] else "artifact_not_present")
        event = EvidenceLifecycleEvent(
            evidence_id=evidence_id,
            incident_id=item.incident_id,
            action=_ACTION_FOR_STATE[to_state],
            from_state=current.state,
            to_state=to_state,
            expected_version=current.version,
            resulting_version=current.version + 1,
            actor=actor,
            reason=reason,
            created_at=now,
            deletion_proof_sha256=deletion_proof,
            redaction_profile_id=redaction_profile_id,
            reason_codes=tuple(reason_codes),
        )
        self.store.record_evidence_lifecycle(event)
        projection = self.lifecycle(evidence_id)
        if to_state in {EvidenceContentState.EXPIRED, EvidenceContentState.DELETED, EvidenceContentState.MISSING_EXTERNAL}:
            reconciliation = self.claim_reconciliation(item.incident_id)
            self.store.record_evidence_reevaluation(EvidenceReevaluationRecord(
                incident_id=item.incident_id,
                evidence_id=evidence_id,
                trigger_action=event.action,
                decision="claim_links_reconciled_without_incident_state_mutation",
                created_at=now,
                active_supporting_links=int(reconciliation["active_supporting_links"]),
                active_contradictory_links=int(reconciliation["active_contradictory_links"]),
                invalidated_links=int(reconciliation["invalidated_links"]),
                incident_state_mutated=False,
                reason_codes=("component_4_review_required_for_hazard_state_change",),
            ))
        return projection

    def enforce_rights_expiry(
        self,
        *,
        now: datetime | None = None,
        actor: str = "system-rights-expiry",
    ) -> tuple[EvidenceLifecycleProjection, ...]:
        now = now or datetime.now(timezone.utc)
        expired: list[EvidenceLifecycleProjection] = []
        for item in self.store.evidence():
            if item.rights_expires_at is None or item.rights_expires_at > now:
                continue
            current = self.lifecycle(item.evidence_id)
            if current.state in {
                EvidenceContentState.AVAILABLE,
                EvidenceContentState.METADATA_ONLY,
                EvidenceContentState.REDACTED,
            }:
                expired.append(self.transition(
                    item.evidence_id,
                    to_state=EvidenceContentState.EXPIRED,
                    expected_version=current.version,
                    actor=actor,
                    reason="rights_expiry_reached",
                    now=now,
                ))
        return tuple(expired)

    def create_claim(self, claim: ClaimNode) -> ClaimNode:
        incident = next((item for item in self.store.latest_by_hazard() if item.incident_id == claim.incident_id), None)
        if incident is None or incident.hazard is not claim.hazard:
            raise ValueError("claim must target an existing incident with the same hazard")
        return self.store.record_claim(claim)

    def link(self, link: ClaimEvidenceLink) -> ClaimEvidenceLink:
        return self.store.record_claim_link(link)

    def families(self, incident_id: UUID) -> tuple[EvidenceFamilySummary, ...]:
        items = self.store.evidence(str(incident_id))
        grouped: dict[str, list[EvidenceItem]] = {}
        for item in items:
            assert item.family_id is not None
            grouped.setdefault(item.family_id, []).append(item)
        result: list[EvidenceFamilySummary] = []
        for family_id, family_items in sorted(grouped.items()):
            content_counts = Counter(item.content_sha256 for item in family_items)
            phash_counts = Counter(item.perceptual_hash for item in family_items if item.perceptual_hash)
            exact_duplicates = sum(max(0, count - 1) for count in content_counts.values())
            near_duplicates = sum(max(0, count - 1) for count in phash_counts.values())
            independent_origins = sum(item.independent_origin_proven for item in family_items)
            independence_units = 1 + independent_origins
            result.append(EvidenceFamilySummary(
                family_id=family_id,
                incident_id=incident_id,
                evidence_ids=tuple(item.evidence_id for item in family_items),
                origin_keys=tuple(sorted({item.origin_key for item in family_items})),
                independence_units=independence_units,
                exact_duplicates=exact_duplicates,
                near_duplicates=near_duplicates,
                independent_origins=independent_origins,
            ))
        return tuple(result)

    def claim_reconciliation(self, incident_id: UUID) -> dict[str, object]:
        links = self.store.claim_links(str(incident_id))
        active_supports = 0
        active_contradictions = 0
        invalidated = 0
        for link in links:
            projection = self.lifecycle(link.evidence_id)
            if not projection.claim_eligible:
                invalidated += 1
            elif link.relation is ClaimEvidenceRelation.SUPPORTS:
                active_supports += 1
            elif link.relation is ClaimEvidenceRelation.CONTRADICTS:
                active_contradictions += 1
        return {
            "incident_id": str(incident_id),
            "active_supporting_links": active_supports,
            "active_contradictory_links": active_contradictions,
            "invalidated_links": invalidated,
            "historical_link_count": len(links),
            "history_rewritten": False,
        }

    def trust_snapshot(self, incident_id: UUID) -> TrustDimensionSnapshot:
        items = self.store.evidence(str(incident_id))
        links = self.store.claim_links(str(incident_id))
        claims = self.store.claims(str(incident_id))
        families = self.families(incident_id)
        source_counts = Counter(item.source_standing.value for item in items)
        media_counts = Counter(item.media_integrity.value for item in items)
        extraction_counts = Counter(item.extraction_confidence_state.value for item in items)
        freshness_counts = Counter(item.freshness_state.value for item in items)
        supporting = 0
        contradictions = 0
        invalidated = 0
        for link in links:
            if not self.lifecycle(link.evidence_id).claim_eligible:
                invalidated += 1
            elif link.relation is ClaimEvidenceRelation.SUPPORTS:
                supporting += 1
            elif link.relation is ClaimEvidenceRelation.CONTRADICTS:
                contradictions += 1
        unresolved = sum(claim.status == "open" for claim in claims)
        independence_units = sum(item.independence_units for item in families)
        reasons: list[str] = []
        if contradictions:
            reasons.append("unresolved_contradictions_present")
        if invalidated:
            reasons.append("evidence_links_invalidated_by_lifecycle")
        if any(item.media_integrity is MediaIntegrityState.MANIPULATION_SUSPECT for item in items):
            reasons.append("manipulation_suspect_evidence_present")
        if any(item.extraction_confidence_state in {ExtractionConfidenceState.UNKNOWN, ExtractionConfidenceState.LOW} for item in items):
            reasons.append("extraction_uncertainty_present")
        if any(item.source_standing is SourceStanding.UNKNOWN for item in items):
            reasons.append("unknown_source_standing_present")
        if not items:
            band = "no_evidence"
            reasons.append("no_evidence")
        elif contradictions:
            band = "contested"
        elif independence_units >= 2 and supporting >= 2:
            band = "corroborated"
        elif supporting:
            band = "supported_single_family"
        elif invalidated and links:
            band = "historical_evidence_not_currently_eligible"
        else:
            band = "unlinked_evidence"
        return TrustDimensionSnapshot(
            incident_id=incident_id,
            source_standing_counts=dict(sorted(source_counts.items())),
            media_integrity_counts=dict(sorted(media_counts.items())),
            extraction_confidence_counts=dict(sorted(extraction_counts.items())),
            freshness_counts=dict(sorted(freshness_counts.items())),
            evidence_families=len(families),
            independence_units=independence_units,
            supporting_links=supporting,
            contradictory_links=contradictions,
            invalidated_links=invalidated,
            unresolved_claims=unresolved,
            summary_band=band,
            reason_codes=tuple(sorted(reasons)),
        )

    def graph_digest(self, incident_id: UUID) -> str:
        payload = {
            "evidence": [item.model_dump(mode="json") for item in self.store.evidence(str(incident_id))],
            "lifecycle": [item.model_dump(mode="json") for item in self.lifecycle_events(incident_id)],
            "claims": [item.model_dump(mode="json") for item in self.store.claims(str(incident_id))],
            "links": [item.model_dump(mode="json") for item in self.store.claim_links(str(incident_id))],
            "families": [item.model_dump(mode="json") for item in self.families(incident_id)],
            "reconciliation": self.claim_reconciliation(incident_id),
            "trust": self.trust_snapshot(incident_id).model_dump(mode="json"),
        }
        return sha256_bytes(canonical_json_bytes(payload))
