from datetime import datetime, timedelta, timezone

import pytest

from sentinel_edge.qualification.soil_moisture import SoilMoistureSample, assess_soil_moisture_trend


def test_soil_moisture_trend_exposes_freshness_and_resolution() -> None:
    now = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    result = assess_soil_moisture_trend((
        SoilMoistureSample(observed_at=now-timedelta(hours=1), received_at=now-timedelta(minutes=59), fraction=.2, resolution_m=100, source_id="soil-a"),
        SoilMoistureSample(observed_at=now-timedelta(minutes=5), received_at=now-timedelta(minutes=4), fraction=.5, resolution_m=100, source_id="soil-a"),
    ), now=now, max_age_seconds=600)
    assert result.trend == "rising"
    assert result.fresh is True
    assert result.resolution_m == 100
    assert result.delta_fraction == pytest.approx(.3)


def test_soil_moisture_stale_or_mixed_source_is_rejected() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    sample = SoilMoistureSample(observed_at=now-timedelta(hours=2), received_at=now-timedelta(hours=2), fraction=.2, resolution_m=30, source_id="soil-a")
    assert assess_soil_moisture_trend((sample,), now=now, max_age_seconds=60).fresh is False
    with pytest.raises(ValueError):
        assess_soil_moisture_trend((sample, sample.model_copy(update={"source_id": "soil-b"})), now=now, max_age_seconds=60)
