import pytest

from sentinel_edge.collector import SensorFrameRejected, decode_sensor_frame, encode_sensor_frame


def test_sensor_frame_round_trip_is_versioned_and_crc_protected() -> None:
    payload = {"sequence": 4, "x": 0.1, "z": 9.8}
    encoded = encode_sensor_frame(payload)
    assert encoded[:2] == b"SE"
    assert decode_sensor_frame(encoded) == payload


@pytest.mark.parametrize("mutator, message", [
    (lambda value: value[:-1], "truncated"),
    (lambda value: value[:6] + bytes([value[6] ^ 1]) + value[7:], "CRC"),
    (lambda value: b"XX" + value[2:], "magic"),
    (lambda value: value[:2] + b"\x02" + value[3:], "version"),
])
def test_sensor_frame_rejects_corrupt_or_unsupported_frames(mutator, message: str) -> None:
    encoded = encode_sensor_frame({"sequence": 1})
    with pytest.raises(SensorFrameRejected, match=message):
        decode_sensor_frame(mutator(encoded))


def test_sensor_frame_rejects_oversized_payload() -> None:
    with pytest.raises(SensorFrameRejected, match="exceeds"):
        encode_sensor_frame({"data": "x" * 100}, max_payload_bytes=16)
    encoded = encode_sensor_frame({"data": "x" * 100}, max_payload_bytes=512)
    with pytest.raises(SensorFrameRejected, match="exceeds"):
        decode_sensor_frame(encoded, max_payload_bytes=16)
