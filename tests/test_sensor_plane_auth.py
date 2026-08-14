import pytest

from sentinel_edge.collector.sensor_protocol import SensorFrameRejected, decode_authenticated_sensor_frame, encode_authenticated_sensor_frame


def test_authenticated_sensor_frame_requires_matching_device_key() -> None:
    frame = encode_authenticated_sensor_frame({"sequence": 1, "value": 2}, device_key=b"device-key")
    assert decode_authenticated_sensor_frame(frame, device_key=b"device-key")["sequence"] == 1
    with pytest.raises(SensorFrameRejected, match="authentication"):
        decode_authenticated_sensor_frame(frame, device_key=b"other-key")


def test_authenticated_sensor_frame_rejects_missing_key() -> None:
    with pytest.raises(SensorFrameRejected, match="device key"):
        encode_authenticated_sensor_frame({"sequence": 1}, device_key=b"")
