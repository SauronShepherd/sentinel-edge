"""Versioned, bounded and CRC-protected sensor-plane frames."""

from __future__ import annotations

import json
import hashlib
import hmac
import struct
import zlib
from typing import Any


class SensorFrameRejected(ValueError):
    """Raised when a sensor-plane frame is malformed or unsafe to process."""


MAGIC = b"SE"
VERSION = 1
HEADER = struct.Struct(">2sBH")  # magic, version, payload length
CRC = struct.Struct(">I")
MIN_FRAME_BYTES = HEADER.size + CRC.size


def encode_sensor_frame(payload: dict[str, Any], *, version: int = VERSION, max_payload_bytes: int = 4096) -> bytes:
    if version != VERSION:
        raise SensorFrameRejected("unsupported sensor frame version")
    try:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SensorFrameRejected("sensor frame payload is not finite JSON") from exc
    if not body or len(body) > min(max_payload_bytes, 0xFFFF):
        raise SensorFrameRejected("sensor frame payload exceeds configured bound")
    header = HEADER.pack(MAGIC, version, len(body))
    return header + body + CRC.pack(zlib.crc32(header + body) & 0xFFFFFFFF)


def decode_sensor_frame(frame: bytes, *, max_payload_bytes: int = 4096) -> dict[str, Any]:
    if max_payload_bytes <= 0:
        raise ValueError("max_payload_bytes must be positive")
    if len(frame) < MIN_FRAME_BYTES:
        raise SensorFrameRejected("sensor frame is truncated")
    magic, version, length = HEADER.unpack(frame[: HEADER.size])
    if magic != MAGIC:
        raise SensorFrameRejected("sensor frame magic mismatch")
    if version != VERSION:
        raise SensorFrameRejected("unsupported sensor frame version")
    if length > max_payload_bytes:
        raise SensorFrameRejected("sensor frame payload exceeds configured bound")
    expected_size = HEADER.size + length + CRC.size
    if len(frame) < expected_size:
        raise SensorFrameRejected("sensor frame is truncated")
    if len(frame) != expected_size:
        raise SensorFrameRejected("sensor frame length mismatch")
    body = frame[HEADER.size : HEADER.size + length]
    actual_crc = CRC.unpack(frame[-CRC.size :])[0]
    if actual_crc != (zlib.crc32(frame[:-CRC.size]) & 0xFFFFFFFF):
        raise SensorFrameRejected("sensor frame CRC mismatch")
    try:
        value = json.loads(body.decode("utf-8"), parse_constant=lambda item: (_ for _ in ()).throw(ValueError(item)))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise SensorFrameRejected("sensor frame payload is not finite JSON") from exc
    if not isinstance(value, dict):
        raise SensorFrameRejected("sensor frame payload must be an object")
    return value


AUTH_TAG_BYTES = hashlib.sha256().digest_size


def encode_authenticated_sensor_frame(payload: dict[str, Any], *, device_key: bytes, version: int = VERSION, max_payload_bytes: int = 4096) -> bytes:
    if not device_key:
        raise SensorFrameRejected("sensor device key is required")
    frame = encode_sensor_frame(payload, version=version, max_payload_bytes=max_payload_bytes)
    return frame + hmac.new(device_key, frame, hashlib.sha256).digest()


def decode_authenticated_sensor_frame(frame: bytes, *, device_key: bytes, max_payload_bytes: int = 4096) -> dict[str, Any]:
    if not device_key:
        raise SensorFrameRejected("sensor device key is required")
    if len(frame) <= AUTH_TAG_BYTES:
        raise SensorFrameRejected("authenticated sensor frame is truncated")
    body, tag = frame[:-AUTH_TAG_BYTES], frame[-AUTH_TAG_BYTES:]
    if not hmac.compare_digest(hmac.new(device_key, body, hashlib.sha256).digest(), tag):
        raise SensorFrameRejected("sensor frame authentication failed")
    return decode_sensor_frame(body, max_payload_bytes=max_payload_bytes)
