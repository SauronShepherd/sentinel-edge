from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sentinel_edge.domain.models import (
    AnalysisResult,
    CoverageState,
    HazardKind,
    IncidentCandidate,
    IncidentIdentityOutcome,
    IncidentState,
)
from sentinel_edge.incidents import IncidentEventEngine, IncidentIdentityService
from sentinel_edge.storage import IncidentJournalStore


def test_temporal_spatial_event_storm_maps_to_one_incident_and_bounded_notification() -> None:
    store = IncidentJournalStore()
    identities = IncidentIdentityService(store)
    incidents = IncidentEventEngine(store)
    base = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
    decisions = []
    for index in range(10):
        candidate = IncidentCandidate(
            hazard=HazardKind.WILDFIRE,
            observed_at=base + timedelta(seconds=index * 10),
            latitude=40.4168 + index * 0.00001,
            longitude=-3.7038,
            horizontal_uncertainty_m=20,
            temporal_window_seconds=300,
            spatial_window_m=500,
            source_id=f"camera-{index % 2}",
            source_event_id=None,
        )
        decision = identities.resolve(candidate)
        decisions.append(decision)
        analysis = AnalysisResult(
            observation_id=uuid4(),
            hazard=HazardKind.WILDFIRE,
            score=0.8,
            state_hint=IncidentState.SUSPECTED,
            features={},
            coverage=CoverageState.SUFFICIENT,
            produced_at=candidate.observed_at,
        )
        incidents.apply_analysis(identities.bind_analysis(analysis, decision), candidate.observed_at)

    assert decisions[0].outcome is IncidentIdentityOutcome.NEW
    assert all(item.incident_id == decisions[0].incident_id for item in decisions)
    assert all(item.outcome is IncidentIdentityOutcome.DUPLICATE for item in decisions[1:])
    assert len(incidents.current()) == 1
    assert len(incidents.notifications()) == 1
    assert len(identities.store.identity_decisions()) == 10


def test_identity_is_hazard_specific_even_at_same_place_and_time() -> None:
    store = IncidentJournalStore()
    service = IncidentIdentityService(store)
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
    wildfire = service.resolve(IncidentCandidate(
        hazard=HazardKind.WILDFIRE,
        observed_at=now,
        latitude=40.0,
        longitude=-3.0,
        source_id="source-a",
        source_event_id="event-1",
    ))
    landslide = service.resolve(IncidentCandidate(
        hazard=HazardKind.LANDSLIDE,
        observed_at=now,
        latitude=40.0,
        longitude=-3.0,
        source_id="source-a",
        source_event_id="event-1",
    ))
    assert wildfire.outcome is IncidentIdentityOutcome.NEW
    assert landslide.outcome is IncidentIdentityOutcome.NEW
    assert wildfire.incident_id != landslide.incident_id
