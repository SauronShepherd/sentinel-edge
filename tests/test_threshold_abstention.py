from datetime import datetime, timezone

from sentinel_edge.domain.models import CoverageState, HazardKind, IncidentState, Observation, SourceMode
from sentinel_edge.hazards.earthquake import EarthquakeAdapter
from sentinel_edge.hazards.wildfire import WildfireAdapter
from sentinel_edge.qualification import decide_with_margin


def observation(hazard: HazardKind, values: dict[str, float]) -> Observation:
    now = datetime(2026, 8, 12, 10, 0, tzinfo=timezone.utc)
    return Observation(source_id="test", hazard=hazard, source_mode=SourceMode.FIXTURE, sequence=1, observed_at=now, received_at=now, values=values, units={key: "1" for key in values})


def test_declared_margin_abstains_at_boundary() -> None:
    decision = decide_with_margin(0.801, thresholds=((0.8, IncidentState.CONFIRMED),), margin=0.01)
    assert decision.abstained is True
    assert decision.state is IncidentState.WATCH


def test_wildfire_near_confirmation_does_not_confirm() -> None:
    result = WildfireAdapter().analyze(observation(HazardKind.WILDFIRE, {
        "smoke_score": 1.0, "flame_score": 0.6166666667, "temporal_persistence": 0.5,
    }))
    assert abs(result.score - 0.81) < 1e-9
    assert result.state_hint is IncidentState.WATCH
    assert result.abstained is True
    assert "decision_threshold_margin_abstention" in result.reason_codes


def test_earthquake_near_confirmation_does_not_confirm() -> None:
    # sqrt(x^2+y^2+z^2)-1 = .6375 gives score .85.
    result = EarthquakeAdapter().analyze(observation(HazardKind.EARTHQUAKE, {
        "accel_x": 1.6375, "accel_y": 0.0, "accel_z": 0.0,
    }))
    assert result.state_hint is IncidentState.WATCH
    assert result.abstained is True
    assert "decision_threshold_margin_abstention" in result.reason_codes
