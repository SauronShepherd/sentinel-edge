from datetime import datetime, timezone

from sentinel_edge.collector import AndroidSensorBridge, HttpIngressAdapter, SensorPlaneAdapter, emulate_sensor_plane
from sentinel_edge.domain.models import HazardKind, Observation, SourceMode
from sentinel_edge.evolution import validate_observation_contract


NOW = datetime(2026, 8, 12, 14, 0, tzinfo=timezone.utc)


def base_payload() -> dict[str, object]:
    return {
        "schema_version": "2.0.0", "hazard": "earthquake", "sequence": 1,
        "observed_at": NOW.isoformat(), "received_at": NOW.isoformat(),
        "values": {"accel_x": 0.1, "accel_y": 0.0, "accel_z": 0.0},
        "units": {"accel_x": "g", "accel_y": "g", "accel_z": "g"},
    }


def test_all_active_adapter_paths_emit_the_same_observation_contract() -> None:
    ingress = HttpIngressAdapter().accept(base_payload(), source_id="http-imu").observation
    android = AndroidSensorBridge(source_id="android-imu", boot_id="android-boot", now=lambda: NOW).observation({
        "sequence": 1, "monotonic_ns": 1, "x": 0.1, "y": 0.0, "z": 0.0, "unit": "g",
    })
    sensor = SensorPlaneAdapter(source_id="pico-imu", boot_id="pico-boot").read(
        emulate_sensor_plane(({"sequence": 1, "monotonic_ns": 1, "x": 0.1, "y": 0.0, "z": 0.0, "unit": "g"},)), received_at=NOW,
    )[0]
    for observation in (ingress, android, sensor):
        report = validate_observation_contract(observation)
        assert report.valid is True
        assert report.schema_version == "2.0.0"
        assert report.observation_sha256


def test_contract_report_rejects_empty_values() -> None:
    observation = Observation(
        hazard=HazardKind.EARTHQUAKE, source_id="fixture", source_mode=SourceMode.FIXTURE,
        sequence=1, observed_at=NOW, received_at=NOW, values={"accel_x": 0.1}, units={"accel_x": "g"},
    )
    assert validate_observation_contract(observation).valid is True
