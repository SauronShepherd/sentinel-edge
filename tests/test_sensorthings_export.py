from datetime import datetime, timezone

from sentinel_edge.domain.models import HazardKind, Observation, SourceMode
from sentinel_edge.integrations import export_observation_sensorthings


def test_sensorthings_export_preserves_linkage() -> None:
    now = datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc)
    observation = Observation(source_id="imu-a", hazard=HazardKind.EARTHQUAKE, source_mode=SourceMode.FIXTURE, sequence=1, observed_at=now, received_at=now, values={"accel_x": 0.1, "accel_z": 9.8}, units={"accel_x": "g", "accel_z": "g"})
    export = export_observation_sensorthings(observation)
    assert export.schema == "ogc-sensorthings-1.1"
    assert export.thing["@iot.id"] == "thing:imu-a"
    assert export.sensor["@iot.id"] == "sensor:imu-a"
    assert len(export.datastreams) == 2
    for stream in export.datastreams:
        assert stream["Thing"]["@iot.id"] == export.thing["@iot.id"]
        assert stream["Sensor"]["@iot.id"] == export.sensor["@iot.id"]
        assert stream["ObservedProperty"]["@iot.id"] in {item["@iot.id"] for item in export.observed_properties}
        assert any(item["Datastream"]["@iot.id"] == stream["@iot.id"] for item in export.observations)
