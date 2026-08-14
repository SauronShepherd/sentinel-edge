import pytest
from pydantic import ValidationError

from sentinel_edge.integrations.raster_context import StaticRasterContext


def test_static_raster_resolution_and_uncertainty_remain_visible() -> None:
    context = StaticRasterContext(source_id="terrain-dem", resolution_m=30.0, uncertainty=12.0)
    payload = context.model_dump(mode="json")
    assert payload["resolution_m"] == 30.0
    assert payload["uncertainty"] == 12.0
    assert "not an exact local measurement" in payload["display_label"]


def test_static_raster_cannot_be_presented_as_exact_measurement() -> None:
    with pytest.raises(ValidationError):
        StaticRasterContext(
            source_id="terrain-dem", resolution_m=30.0, uncertainty=12.0,
            context_only=False, display_label="terrain measurement",
        )
