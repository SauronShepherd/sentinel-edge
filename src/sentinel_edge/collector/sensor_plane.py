"""Optional Pico/Cortex-M33 sensor-plane adapter and deterministic emulator."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from sentinel_edge.collector.sensor_protocol import SensorFrameRejected, decode_sensor_frame, encode_sensor_frame
from sentinel_edge.domain.models import HazardKind, ImuSample, Observation, SourceMode


class SensorPlaneUnavailable(RuntimeError):
    """Raised when the optional sensor plane cannot provide a safe frame."""


class SensorPlaneAvailability(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool
    available: bool
    operating_mode: Literal["sensor_plane", "pi_only", "fixture"]
    release_dependency: bool = False
    reason_codes: tuple[str, ...] = ()


def resolve_sensor_plane_availability(*, enabled: bool, available: bool, fixture_mode: bool = False) -> SensorPlaneAvailability:
    """Select an operating path without making the optional plane a dependency."""
    if fixture_mode:
        return SensorPlaneAvailability(
            enabled=enabled, available=available, operating_mode="fixture",
            reason_codes=("fixture_mode", "sensor_plane_optional"),
        )
    if enabled and available:
        return SensorPlaneAvailability(enabled=True, available=True, operating_mode="sensor_plane")
    reason = "sensor_plane_disabled" if not enabled else "sensor_plane_unavailable"
    return SensorPlaneAvailability(
        enabled=enabled, available=available, operating_mode="pi_only",
        reason_codes=(reason, "sensor_plane_optional"),
    )


class SensorPlaneAdapter:
    """Normalize the same framed protocol from hardware or emulator input."""

    def __init__(
        self,
        *,
        source_id: str,
        boot_id: str,
        max_payload_bytes: int = 4096,
        max_frames: int = 256,
        clock_epoch: int = 0,
    ) -> None:
        if not source_id.strip() or not boot_id.strip():
            raise ValueError("source_id and boot_id must not be blank")
        if max_payload_bytes <= 0 or max_frames <= 0 or clock_epoch < 0:
            raise ValueError("sensor-plane bounds must be positive")
        self.source_id = source_id
        self.boot_id = boot_id
        self.max_payload_bytes = max_payload_bytes
        self.max_frames = max_frames
        self.clock_epoch = clock_epoch
        self._last_sequence: int | None = None

    def read(self, frames: Iterable[bytes], *, received_at: datetime | None = None) -> tuple[Observation, ...]:
        now = received_at or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        observations: list[Observation] = []
        for frame in frames:
            if len(observations) >= self.max_frames:
                raise SensorPlaneUnavailable("sensor-plane frame bound exceeded")
            try:
                payload = decode_sensor_frame(frame, max_payload_bytes=self.max_payload_bytes)
                sample = ImuSample.model_validate(payload)
            except (SensorFrameRejected, ValueError, TypeError) as exc:
                raise SensorPlaneUnavailable("sensor-plane frame rejected") from exc
            if self._last_sequence is not None and sample.sequence <= self._last_sequence:
                raise SensorPlaneUnavailable("sensor-plane sequence is not increasing")
            self._last_sequence = sample.sequence
            observations.append(Observation(
                source_id=self.source_id,
                hazard=HazardKind.EARTHQUAKE,
                source_mode=SourceMode.LIVE,
                boot_id=self.boot_id,
                sequence=sample.sequence,
                observed_at=now,
                received_at=now,
                values={"accel_x": sample.x, "accel_y": sample.y, "accel_z": sample.z},
                units={"accel_x": sample.unit, "accel_y": sample.unit, "accel_z": sample.unit},
                source_lineage="cortex-m33-sensor-plane",
                clock_epoch=self.clock_epoch,
            ))
        return tuple(observations)


def emulate_sensor_plane(samples: Iterable[dict[str, Any]], *, max_payload_bytes: int = 4096) -> tuple[bytes, ...]:
    """Produce protocol-identical frames for deterministic offline commissioning."""
    return tuple(encode_sensor_frame(sample, max_payload_bytes=max_payload_bytes) for sample in samples)
