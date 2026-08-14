"""Bounded OGC SensorThings-style linkage for normalized observations."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from sentinel_edge.domain.models import Observation


class SensorThingsExport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema: str = "ogc-sensorthings-1.1"
    thing: dict[str, Any]
    sensor: dict[str, Any]
    observed_properties: tuple[dict[str, Any], ...]
    datastreams: tuple[dict[str, Any], ...]
    observations: tuple[dict[str, Any], ...]


def export_observation_sensorthings(observation: Observation, *, thing_name: str | None = None) -> SensorThingsExport:
    thing_id = f"thing:{observation.source_id}"
    sensor_id = f"sensor:{observation.source_id}"
    thing = {"@iot.id": thing_id, "name": thing_name or observation.source_id}
    sensor = {"@iot.id": sensor_id, "name": observation.source_id, "encodingType": "application/json"}
    properties = tuple({"@iot.id": f"property:{key}", "name": key} for key in sorted(observation.values))
    datastreams = tuple({
        "@iot.id": f"datastream:{observation.source_id}:{key}",
        "name": key,
        "unitOfMeasurement": {"symbol": observation.units[key]},
        "Thing": {"@iot.id": thing_id},
        "Sensor": {"@iot.id": sensor_id},
        "ObservedProperty": {"@iot.id": f"property:{key}"},
    } for key in sorted(observation.values))
    observations = tuple({
        "@iot.id": f"observation:{observation.observation_id}:{key}",
        "phenomenonTime": observation.observed_at.isoformat(),
        "result": observation.values[key],
        "Datastream": {"@iot.id": f"datastream:{observation.source_id}:{key}"},
    } for key in sorted(observation.values))
    return SensorThingsExport(thing=thing, sensor=sensor, observed_properties=properties, datastreams=datastreams, observations=observations)
