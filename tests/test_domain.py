from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from sentinel_edge.domain.models import BoundaryEnvelope, HazardKind, Observation, SourceMode


def test_observation_requires_units_for_every_value() -> None:
    with pytest.raises(ValidationError):
        Observation(source_id="x", hazard=HazardKind.FLOOD, source_mode=SourceMode.FIXTURE, sequence=1,
                    observed_at=datetime.now(timezone.utc), received_at=datetime.now(timezone.utc),
                    values={"water_level_m": 1.0}, units={})


def test_boundary_envelope_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        BoundaryEnvelope[dict](schema_name="x", producer_component="component-1", payload={}, unexpected=True)
