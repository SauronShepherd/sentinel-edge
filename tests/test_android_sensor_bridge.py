from datetime import datetime, timezone

import pytest

from sentinel_edge.collector import AndroidBridgeRejected, AndroidSensorBridge, StreamingSourceCollector


NOW = datetime(2026, 8, 12, 10, 0, tzinfo=timezone.utc)


def frame(sequence: int, *, observed_at: str | None = None) -> dict[str, object]:
    value: dict[str, object] = {
        "sequence": sequence,
        "monotonic_ns": sequence * 10_000_000,
        "x": 0.1,
        "y": 0.2,
        "z": 9.8,
        "unit": "m/s2",
        "clock_uncertainty_ms": 4.5,
    }
    if observed_at is not None:
        value["observed_at"] = observed_at
    return value


def test_android_frames_normalize_to_live_observations_and_collector_contract() -> None:
    bridge = AndroidSensorBridge(source_id="phone-imu", boot_id="android-boot", now=lambda: NOW)
    observations = bridge.stream([frame(0), frame(1)])

    assert observations[0].source_mode.value == "live"
    assert observations[0].source_lineage == "android-sensor-bridge"
    assert observations[0].clock_uncertainty_ms == 4.5
    assert observations[0].values["accel_z"] == 9.8

    collector = StreamingSourceCollector()
    collector.configure_source("phone-imu", source_kind="imu", location="android-local")
    collector.ingest(observations[0])
    collector.ingest(observations[1])
    assert collector._buffers["phone-imu"].latest().sequence == 1


def test_android_bridge_rejects_future_nonfinite_and_oversized_frames() -> None:
    bridge = AndroidSensorBridge(source_id="phone-imu", boot_id="android-boot", max_frame_bytes=100, now=lambda: NOW)
    with pytest.raises(AndroidBridgeRejected):
        bridge.observation({**frame(0), "x": float("nan")})
    with pytest.raises(AndroidBridgeRejected):
        bridge.observation({**frame(0), "observed_at": "2026-08-12T10:00:01+00:00"})
    with pytest.raises(AndroidBridgeRejected):
        bridge.observation({**frame(0), "padding": "x" * 200})


def test_android_bridge_stream_is_bounded() -> None:
    bridge = AndroidSensorBridge(source_id="phone-imu", boot_id="android-boot", max_frames=1, now=lambda: NOW)
    with pytest.raises(AndroidBridgeRejected, match="frame bound"):
        bridge.stream([frame(0), frame(1)])
