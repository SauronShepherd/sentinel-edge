from datetime import datetime, timezone

from sentinel_edge.analysis import build_decision_trace
from sentinel_edge.domain.models import HazardKind, IncidentState, Observation, SourceMode
from sentinel_edge.hazards import WildfireAdapter


def _observation(**values: float) -> Observation:
    return Observation(
        source_id="camera-trace", hazard=HazardKind.WILDFIRE, source_mode=SourceMode.FIXTURE,
        sequence=1, observed_at=datetime(2026, 8, 12, tzinfo=timezone.utc),
        received_at=datetime(2026, 8, 12, tzinfo=timezone.utc), values=values,
        units={key: "ratio" for key in values},
    )


def test_decision_trace_contains_positive_and_blocking_reasons() -> None:
    result = WildfireAdapter().analyze(_observation(smoke_score=1.0, flame_score=1.0, temporal_persistence=0.0))
    trace = build_decision_trace(result)
    assert trace["schema"] == "sentinel-edge-decision-trace/1.0"
    assert trace["outcome"] == "not_escalated"
    assert trace["positive_reasons"]
    assert "temporal_persistence_insufficient" in trace["blocking_reasons"]


def test_decision_trace_marks_escalated_result() -> None:
    result = WildfireAdapter().analyze(_observation(smoke_score=1.0, flame_score=1.0, temporal_persistence=1.0))
    trace = build_decision_trace(result)
    assert result.state_hint in {IncidentState.SUSPECTED, IncidentState.CONFIRMED}
    assert trace["outcome"] == "escalated"
    assert "score_positive" in trace["positive_reasons"] or trace["positive_reasons"]
