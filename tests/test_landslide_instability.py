from datetime import datetime, timezone

from sentinel_edge.domain.models import HazardKind, Observation, SourceMode
from sentinel_edge.hazards import LandslideAdapter


def test_landslide_optional_instability_exposes_uncertainty_and_features() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    observation = Observation(source_id="slope", hazard=HazardKind.LANDSLIDE, source_mode=SourceMode.FIXTURE,
        sequence=1, observed_at=now, received_at=now,
        values={"tilt_rate_deg_h": .2, "vibration_rms": .1}, units={"tilt_rate_deg_h": "deg/h", "vibration_rms": "rms"})
    result = LandslideAdapter(instability_predictor=lambda _: .7, instability_uncertainty=.1,
                              instability_profile_id="site-profile-v1").analyze(observation)
    assert result.features["instability_available"] == 1.0
    assert result.features["instability_uncertainty"] == .1
    assert "validated_instability_available" in result.reason_codes


def test_landslide_instability_failure_keeps_deterministic_path() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    observation = Observation(source_id="slope", hazard=HazardKind.LANDSLIDE, source_mode=SourceMode.FIXTURE,
        sequence=1, observed_at=now, received_at=now,
        values={"tilt_rate_deg_h": .2, "vibration_rms": .1}, units={"tilt_rate_deg_h": "deg/h", "vibration_rms": "rms"})
    result = LandslideAdapter(instability_predictor=lambda _: 2.0).analyze(observation)
    assert result.features["instability_available"] == 0.0
    assert "instability_failed_deterministic_fallback" in result.reason_codes
