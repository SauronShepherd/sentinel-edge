from datetime import datetime, timezone

import pytest

from sentinel_edge.collector import SensorPlaneAdapter, SensorPlaneUnavailable, emulate_sensor_plane


NOW = datetime(2026, 8, 12, 11, 0, tzinfo=timezone.utc)


def sample(sequence: int) -> dict[str, object]:
    return {"sequence": sequence, "monotonic_ns": sequence * 10_000_000, "x": 0.1, "y": 0.2, "z": 9.8, "unit": "m/s2"}


def test_emulator_and_sensor_plane_use_the_same_protocol() -> None:
    frames = emulate_sensor_plane([sample(0), sample(1)])
    observations = SensorPlaneAdapter(source_id="pico-imu", boot_id="pico-boot").read(frames, received_at=NOW)
    assert [item.sequence for item in observations] == [0, 1]
    assert observations[0].source_mode.value == "live"
    assert observations[0].source_lineage == "cortex-m33-sensor-plane"


def test_sensor_plane_rejects_corrupt_disconnect_and_replay() -> None:
    frames = list(emulate_sensor_plane([sample(1), sample(1)]))
    adapter = SensorPlaneAdapter(source_id="pico-imu", boot_id="pico-boot")
    adapter.read(frames[:1], received_at=NOW)
    with pytest.raises(SensorPlaneUnavailable, match="not increasing"):
        adapter.read(frames[1:], received_at=NOW)
    with pytest.raises(SensorPlaneUnavailable, match="rejected"):
        SensorPlaneAdapter(source_id="pico-imu", boot_id="pico-boot").read([frames[0][:-1]], received_at=NOW)


def test_sensor_plane_frame_count_is_bounded() -> None:
    frames = emulate_sensor_plane([sample(0), sample(1)])
    with pytest.raises(SensorPlaneUnavailable, match="bound"):
        SensorPlaneAdapter(source_id="pico-imu", boot_id="pico-boot", max_frames=1).read(frames, received_at=NOW)
