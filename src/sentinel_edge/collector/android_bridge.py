"""Bounded local Android IMU bridge.

The Android side is expected to hand this adapter newline-delimited JSON frames
over a local transport (for example USB/ADB or a local socket).  This module
only normalizes frames; it does not open a network connection or classify them.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from sentinel_edge.domain.models import HazardKind, Observation, SourceMode


class AndroidBridgeRejected(ValueError):
    """Raised when a mobile sensor frame cannot enter the observation contract."""


class AndroidImuFrame(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sequence: int = Field(ge=0)
    monotonic_ns: int = Field(ge=0)
    x: float
    y: float
    z: float
    unit: str = "m/s^2"
    observed_at: datetime | None = None
    clock_uncertainty_ms: float = Field(default=0.0, ge=0.0)


class AndroidSensorBridge:
    """Normalize a bounded stream from one locally connected Android device."""

    def __init__(
        self,
        *,
        source_id: str,
        boot_id: str,
        clock_epoch: int = 0,
        hazard: HazardKind = HazardKind.EARTHQUAKE,
        max_frame_bytes: int = 16 * 1024,
        max_frames: int = 256,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        if not source_id.strip() or not boot_id.strip():
            raise ValueError("source_id and boot_id must not be blank")
        if clock_epoch < 0 or max_frame_bytes <= 0 or max_frames <= 0:
            raise ValueError("bridge bounds must be positive")
        self.source_id = source_id
        self.boot_id = boot_id
        self.clock_epoch = clock_epoch
        self.hazard = hazard
        self.max_frame_bytes = max_frame_bytes
        self.max_frames = max_frames
        self._now = now or (lambda: datetime.now(timezone.utc))

    def _decode(self, payload: bytes | str | dict[str, Any]) -> AndroidImuFrame:
        if isinstance(payload, dict):
            try:
                raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
            except (TypeError, ValueError) as exc:
                raise AndroidBridgeRejected("Android IMU frame is not finite JSON") from exc
            value = payload
        elif isinstance(payload, str):
            raw = payload.encode("utf-8")
            value = self._parse(raw)
        elif isinstance(payload, bytes):
            raw = payload
            value = self._parse(raw)
        else:
            raise AndroidBridgeRejected("Android IMU frame must be JSON bytes, text, or an object")
        if not raw or len(raw) > self.max_frame_bytes:
            raise AndroidBridgeRejected("Android IMU frame exceeds configured byte bound")
        try:
            return AndroidImuFrame.model_validate(value)
        except Exception as exc:
            raise AndroidBridgeRejected("Android IMU frame failed validation") from exc

    @staticmethod
    def _parse(raw: bytes) -> dict[str, Any]:
        try:
            value = json.loads(raw.decode("utf-8"), parse_constant=lambda item: (_ for _ in ()).throw(ValueError(item)))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise AndroidBridgeRejected("Android IMU frame is not finite JSON") from exc
        if not isinstance(value, dict):
            raise AndroidBridgeRejected("Android IMU frame must be a JSON object")
        return value

    def observation(self, payload: bytes | str | dict[str, Any]) -> Observation:
        frame = self._decode(payload)
        received_at = self._now()
        if received_at.tzinfo is None:
            received_at = received_at.replace(tzinfo=timezone.utc)
        observed_at = frame.observed_at or received_at
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        if observed_at > received_at:
            raise AndroidBridgeRejected("Android sensor event cannot be in the future")
        return Observation(
            source_id=self.source_id,
            hazard=self.hazard,
            source_mode=SourceMode.LIVE,
            boot_id=self.boot_id,
            sequence=frame.sequence,
            observed_at=observed_at,
            received_at=received_at,
            values={"accel_x": frame.x, "accel_y": frame.y, "accel_z": frame.z},
            units={"accel_x": frame.unit.replace("m/s^2", "m/s2"), "accel_y": frame.unit.replace("m/s^2", "m/s2"), "accel_z": frame.unit.replace("m/s^2", "m/s2")},
            source_lineage="android-sensor-bridge",
            clock_epoch=self.clock_epoch,
            clock_uncertainty_ms=frame.clock_uncertainty_ms,
        )

    def stream(self, payloads: Iterable[bytes | str | dict[str, Any]]) -> tuple[Observation, ...]:
        observations: list[Observation] = []
        for payload in payloads:
            if len(observations) >= self.max_frames:
                raise AndroidBridgeRejected("Android IMU stream exceeds configured frame bound")
            observations.append(self.observation(payload))
        return tuple(observations)
