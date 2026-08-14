from __future__ import annotations

import math
from uuid import NAMESPACE_URL, uuid5

from sentinel_edge.domain.models import (
    AnalysisResult,
    IncidentCandidate,
    IncidentIdentityDecision,
    IncidentIdentityOutcome,
)
from sentinel_edge.storage import IncidentJournalStore


def _distance_m(left: IncidentCandidate, right: IncidentCandidate) -> float:
    radius = 6_371_008.8
    lat1 = math.radians(left.latitude)
    lat2 = math.radians(right.latitude)
    dlat = lat2 - lat1
    dlon = math.radians(right.longitude - left.longitude)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1 - a)))


class IncidentIdentityService:
    """Durable temporal-spatial identity resolver; it never merges different hazards."""

    def __init__(self, store: IncidentJournalStore) -> None:
        self.store = store

    @staticmethod
    def _new_incident_id(candidate: IncidentCandidate):
        source_key = candidate.source_event_id or (
            f"{candidate.observed_at.isoformat()}:{candidate.latitude:.5f}:{candidate.longitude:.5f}"
        )
        return uuid5(NAMESPACE_URL, f"sentinel-incident-identity:{candidate.hazard.value}:{source_key}")

    def resolve(self, candidate: IncidentCandidate) -> IncidentIdentityDecision:
        best: tuple[float, float, IncidentCandidate, str, tuple[str, ...]] | None = None
        for prior, incident_id in self.store.incident_candidates(candidate.hazard.value):
            time_delta = abs((candidate.observed_at - prior.observed_at).total_seconds())
            if (
                candidate.source_event_id
                and prior.source_event_id
                and candidate.source_id == prior.source_id
                and candidate.source_event_id == prior.source_event_id
            ):
                best = (0.0, time_delta, prior, incident_id, ("same_source_event_id",))
                break
            time_limit = max(candidate.temporal_window_seconds, prior.temporal_window_seconds)
            if time_delta > time_limit:
                continue
            separation = _distance_m(candidate, prior)
            spatial_limit = max(candidate.spatial_window_m, prior.spatial_window_m)
            spatial_limit += candidate.horizontal_uncertainty_m + prior.horizontal_uncertainty_m
            if separation > spatial_limit:
                continue
            reasons = ("temporal_window_match", "spatial_window_match", "same_hazard")
            if best is None or (separation, time_delta) < (best[0], best[1]):
                best = (separation, time_delta, prior, incident_id, reasons)
        if best is None:
            decision = IncidentIdentityDecision(
                decision_id=uuid5(NAMESPACE_URL, f"sentinel-identity-decision:{candidate.candidate_id}"),
                candidate_id=candidate.candidate_id,
                incident_id=self._new_incident_id(candidate),
                outcome=IncidentIdentityOutcome.NEW,
                reason_codes=("no_temporal_spatial_duplicate", "hazard_specific_identity"),
            )
        else:
            separation, time_delta, prior, incident_id, reasons = best
            decision = IncidentIdentityDecision(
                decision_id=uuid5(NAMESPACE_URL, f"sentinel-identity-decision:{candidate.candidate_id}"),
                candidate_id=candidate.candidate_id,
                incident_id=incident_id,
                outcome=IncidentIdentityOutcome.DUPLICATE,
                matched_candidate_id=prior.candidate_id,
                separation_m=separation,
                time_delta_seconds=time_delta,
                reason_codes=reasons,
            )
        return self.store.record_identity_decision(candidate, decision)

    @staticmethod
    def bind_analysis(analysis: AnalysisResult, decision: IncidentIdentityDecision) -> AnalysisResult:
        if analysis.hazard.value not in {"wildfire", "flood", "earthquake", "landslide"}:
            raise ValueError("unsupported hazard")
        return analysis.model_copy(update={"incident_id_hint": decision.incident_id})
