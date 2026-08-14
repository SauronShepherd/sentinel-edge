from datetime import datetime, timedelta, timezone

import pytest

from sentinel_edge.qualification.landslide_context import (
    LandslideContextKind, LandslideContextRecord, display_landslide_context,
)


def test_terrain_context_preserves_static_provenance() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    record = LandslideContextRecord(kind=LandslideContextKind.BD_MOVES_TERRAIN, record_id="terrain-1",
        source_provenance="fixture:bd-moves:v1", observed_at=now-timedelta(days=30), received_at=now,
        resolution_m=30)
    shown = display_landslide_context(record, now=now)
    assert shown.source_provenance == "fixture:bd-moves:v1"
    assert shown.historical_only is False
    assert shown.decision_influence_allowed is False


def test_swi_context_exposes_timeliness_and_resolution() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    shown = display_landslide_context(LandslideContextRecord(
        kind=LandslideContextKind.COPERNICUS_SOIL_WATER_INDEX, record_id="swi-1",
        source_provenance="fixture:copernicus:swi", observed_at=now-timedelta(hours=4), received_at=now,
        resolution_m=1000, value=.62), now=now)
    assert shown.age_seconds == 14400
    assert shown.resolution_m == 1000


def test_egms_is_historical_only() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        LandslideContextRecord(kind=LandslideContextKind.EGMS_DEFORMATION, record_id="egms-1",
            source_provenance="fixture:egms", observed_at=now, received_at=now)
    record = LandslideContextRecord(kind=LandslideContextKind.EGMS_DEFORMATION, record_id="egms-1",
        source_provenance="fixture:egms", observed_at=now, received_at=now, historical_only=True)
    assert display_landslide_context(record, now=now).historical_only is True
