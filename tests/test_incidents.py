from datetime import datetime, timezone
from uuid import uuid4

from sentinel_edge.domain.models import AnalysisResult, CoverageState, HazardKind, IncidentState
from sentinel_edge.incidents import IncidentEventEngine


def result(score: float, state: IncidentState, coverage: CoverageState = CoverageState.SUFFICIENT, abstained: bool = False) -> AnalysisResult:
    return AnalysisResult(observation_id=uuid4(), hazard=HazardKind.WILDFIRE, score=score,
                          state_hint=state, features={}, coverage=coverage, abstained=abstained)


def test_component_four_owns_ordered_incident_versions() -> None:
    engine = IncidentEventEngine()
    first = engine.apply_analysis(result(0.6, IncidentState.SUSPECTED))
    second = engine.apply_analysis(result(0.9, IncidentState.CONFIRMED))
    assert (first.version, second.version) == (1,2)
    assert len(engine.journal()) == 2


def test_blind_or_abstained_analysis_cannot_strengthen_state() -> None:
    engine = IncidentEventEngine()
    record = engine.apply_analysis(result(0.95, IncidentState.CONFIRMED, CoverageState.BLIND, True))
    assert record.state is IncidentState.DEGRADED


def test_replayed_analysis_is_idempotent_and_does_not_advance_incident_version() -> None:
    engine = IncidentEventEngine()
    analysis = result(0.6, IncidentState.SUSPECTED)

    first = engine.apply_analysis(analysis)
    replay = engine.apply_analysis(analysis.model_copy(update={"state_hint": IncidentState.CONFIRMED, "score": 0.99}))

    assert replay == first
    assert replay.version == 1
    assert len(engine.journal()) == 1


def test_backfill_preserves_event_time_when_acceptance_is_later() -> None:
    event_time = datetime(2026, 8, 1, tzinfo=timezone.utc)
    accepted_at = datetime(2026, 8, 12, tzinfo=timezone.utc)
    analysis = result(0.6, IncidentState.SUSPECTED).model_copy(update={"event_time": event_time, "produced_at": accepted_at})
    record = IncidentEventEngine().apply_analysis(analysis, accepted_at=accepted_at)
    assert record.first_observed_at == event_time
    assert record.last_observed_at == accepted_at
    assert record.first_observed_at < record.last_observed_at


def test_late_context_updates_history_without_fresh_notification() -> None:
    engine = IncidentEventEngine()
    accepted = datetime(2026, 8, 12, tzinfo=timezone.utc)
    first = engine.apply_analysis(result(0.6, IncidentState.SUSPECTED).model_copy(update={"event_time": accepted}), accepted_at=accepted)
    late = result(0.9, IncidentState.CONFIRMED).model_copy(update={"event_time": datetime(2026, 8, 1, tzinfo=timezone.utc)})
    corrected = engine.apply_analysis(late, accepted_at=accepted)
    assert corrected.version == first.version + 1
    assert corrected.state is first.state
    assert corrected.event_time_watermark == first.event_time_watermark
    assert "late_context_correction" in corrected.reason_codes
    assert len(engine.notifications()) == 1


def test_hazard_specific_incident_ids_cannot_collide_across_hazards() -> None:
    engine = IncidentEventEngine()
    wildfire = engine.apply_analysis(result(0.6, IncidentState.SUSPECTED))
    earthquake = engine.apply_analysis(
        result(0.7, IncidentState.SUSPECTED).model_copy(update={"hazard": HazardKind.EARTHQUAKE})
    )

    assert wildfire.hazard is HazardKind.WILDFIRE
    assert earthquake.hazard is HazardKind.EARTHQUAKE
    assert wildfire.incident_id != earthquake.incident_id
    assert {item.hazard for item in engine.current()} == {HazardKind.WILDFIRE, HazardKind.EARTHQUAKE}


def test_analysis_and_incident_preserve_source_model_and_config_lineage() -> None:
    from sentinel_edge.analysis import AnalysisEnrichmentEngine
    from sentinel_edge.domain.models import Observation, SourceMode
    observation = Observation(
        source_id="lineage-camera", hazard=HazardKind.WILDFIRE, source_mode=SourceMode.FIXTURE,
        source_lineage="camera-capture-v3", sequence=1,
        observed_at=datetime.now(timezone.utc), received_at=datetime.now(timezone.utc),
        values={"smoke_score": 0.7, "flame_score": 0.1, "temporal_persistence": 0.6},
        units={"smoke_score": "ratio", "flame_score": "ratio", "temporal_persistence": "ratio"},
    )
    analysis = AnalysisEnrichmentEngine().analyze(observation).model_copy(update={"config_hashes": ("a" * 64,)})
    record = IncidentEventEngine().apply_analysis(analysis)

    assert (analysis.source_lineage, analysis.model_profile_id, analysis.config_hashes) == (
        "camera-capture-v3", "wildfire-deterministic-v2", ("a" * 64,)
    )
    assert (record.source_lineage, record.model_profile_id, record.config_hashes) == (
        "camera-capture-v3", "wildfire-deterministic-v2", ("a" * 64,)
    )


def test_incident_labels_are_append_only_and_audit_each_analysis() -> None:
    engine = IncidentEventEngine()
    first = engine.apply_analysis(result(0.6, IncidentState.SUSPECTED))
    second = engine.apply_analysis(result(0.9, IncidentState.CONFIRMED))

    assert tuple(label.value for label in first.labels) == ("reject",)
    assert tuple(label.value for label in second.labels) == ("reject", "confirm")
    assert tuple(tuple(label.value for label in item.labels) for item in engine.journal()) == (("reject",), ("reject", "confirm"))
