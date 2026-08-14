from datetime import datetime, timezone

import pytest

from sentinel_edge.domain.models import HazardKind, Observation, SourceMode
from sentinel_edge.hazards import FloodAdapter, ForecastMetadata


def observation() -> Observation:
    now = datetime(2026, 8, 12, 10, 0, tzinfo=timezone.utc)
    return Observation(source_id="river", hazard=HazardKind.FLOOD, source_mode=SourceMode.FIXTURE, sequence=1, observed_at=now, received_at=now, values={"water_level_m": 1.0, "rate_of_rise_m_per_h": 0.2}, units={"water_level_m": "m", "rate_of_rise_m_per_h": "m/h"})


def test_forecast_requires_horizon_uncertainty_and_profile() -> None:
    with pytest.raises(ValueError):
        ForecastMetadata.from_prediction(0.5, horizon_seconds=0, uncertainty=0.2, profile_id="x")
    result = ForecastMetadata.from_prediction(0.5, horizon_seconds=1800, uncertainty=0.1, profile_id="flood-v1")
    assert result.feature_values()["forecast_horizon_seconds"] == 1800.0
    assert result.feature_values()["forecast_uncertainty"] == 0.1


def test_flood_marks_forecast_not_applicable_without_learned_profile() -> None:
    result = FloodAdapter().analyze(observation())
    assert result.features["forecast_available"] == 0.0
    assert "forecast_not_applicable" in result.reason_codes


def test_flood_exposes_horizon_and_uncertainty_for_learned_forecast() -> None:
    result = FloodAdapter(
        forecast_predictor=lambda _: 0.7,
        forecast_horizon_seconds=1800,
        forecast_uncertainty=0.15,
        forecast_profile_id="flood-site-v1",
    ).analyze(observation())
    assert result.features["forecast_available"] == 1.0
    assert result.features["forecast_horizon_seconds"] == 1800.0
    assert result.features["forecast_uncertainty"] == 0.15
    assert "validated_forecast_available" in result.reason_codes
