from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from pydantic import BaseModel, ConfigDict, field_validator

from sentinel_edge.domain.models import HealthState, Observation, SourceHealth, SourceMode
from sentinel_edge.storage import SourceCursorStore
from sentinel_edge.semantics import MeasurementRegistry


class SourceConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    source_kind: str
    location: str
    max_lateness_seconds: float = 0.0

    @field_validator("source_id", "location")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source configuration values must not be blank")
        return value

    @field_validator("source_kind")
    @classmethod
    def supported_kind(cls, value: str) -> str:
        if value not in {"camera", "imu", "video_fixture", "rtsp"}:
            raise ValueError("source kind must be camera, imu, video_fixture, or rtsp")
        return value

    @field_validator("max_lateness_seconds")
    @classmethod
    def non_negative_lateness(cls, value: float) -> float:
        if value < 0:
            raise ValueError("max_lateness_seconds must be non-negative")
        return value


class BoundedRingBuffer:
    def __init__(self, capacity: int = 256) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._items: deque[Observation] = deque(maxlen=capacity)
        self.dropped = 0
        self._lock = RLock()

    def append(self, observation: Observation) -> None:
        with self._lock:
            if len(self._items) == self.capacity:
                self.dropped += 1
            self._items.append(observation)

    def latest(self) -> Observation | None:
        with self._lock:
            return self._items[-1] if self._items else None

    def snapshot(self) -> tuple[Observation, ...]:
        with self._lock:
            return tuple(self._items)


class StreamingSourceCollector:
    """Component 1: normalized acquisition, validation, bounded buffering, durable cursors, and health."""

    component_id = "component-1-collector"

    def __init__(self, buffer_capacity: int = 256, cursor_store: SourceCursorStore | None = None, measurement_registry: MeasurementRegistry | None = None) -> None:
        self._capacity = buffer_capacity
        self.measurements = measurement_registry or MeasurementRegistry()
        self._buffers: dict[str, BoundedRingBuffer] = {}
        self._cursor_store = cursor_store or SourceCursorStore()
        self._health: dict[str, SourceHealth] = {item.source_id: item for item in self._cursor_store.load_all()}
        self._source_configurations: dict[str, SourceConfiguration] = {}

    def configure_source(self, source_id: str, *, source_kind: str, location: str, max_lateness_seconds: float | None = None) -> SourceConfiguration:
        default_lateness = {"imu": 0.5, "camera": 2.0, "rtsp": 2.0, "video_fixture": 0.0}[source_kind]
        configuration = SourceConfiguration(
            source_id=source_id,
            source_kind=source_kind,
            location=location,
            max_lateness_seconds=default_lateness if max_lateness_seconds is None else max_lateness_seconds,
        )
        previous = self._source_configurations.get(source_id)
        if previous is not None and previous != configuration:
            raise ValueError("source configuration is immutable")
        self._source_configurations[source_id] = configuration
        return configuration

    def source_configurations(self) -> tuple[SourceConfiguration, ...]:
        return tuple(sorted(self._source_configurations.values(), key=lambda item: item.source_id))

    def ingest(self, observation: Observation) -> Observation:
        if observation.source_mode is SourceMode.REPLAYED:
            raise ValueError("replayed observations cannot enter the live collector")
        measurement_report = self.measurements.validate(observation)
        if not measurement_report.valid:
            raise ValueError("measurement contract rejected: " + ",".join(measurement_report.reason_codes))
        previous = self._health.get(observation.source_id)
        configuration = self._source_configurations.get(observation.source_id)
        reasons: list[str] = list(measurement_report.reason_codes)
        state = HealthState.HEALTHY
        if measurement_report.invalid_properties or measurement_report.suspect_properties:
            state = HealthState.DEGRADED
        if previous and previous.last_sequence is not None:
            same_epoch = previous.boot_id == observation.boot_id and previous.clock_epoch == observation.clock_epoch
            if same_epoch and observation.sequence <= previous.last_sequence:
                raise ValueError("sequence must increase per source boot and clock epoch")
            if previous.last_observed_at and observation.observed_at < previous.last_observed_at:
                lateness_seconds = (previous.last_observed_at - observation.observed_at).total_seconds()
                bound = configuration.max_lateness_seconds if configuration is not None else 0.0
                if lateness_seconds > bound:
                    rejected = previous.model_copy(update={
                        "state": HealthState.DEGRADED,
                        "reason_codes": tuple(sorted(set(previous.reason_codes + ("late_event_exceeded",)))),
                    })
                    self._cursor_store.upsert(rejected, recorded_at=observation.received_at)
                    self._health[observation.source_id] = rejected
                    raise ValueError("event time exceeds adapter lateness bound")
                reasons.append("late_event")
                state = HealthState.DEGRADED
            if same_epoch and observation.sequence > previous.last_sequence + 1:
                reasons.append("sequence_gap")
                state = HealthState.DEGRADED
            if not same_epoch:
                reasons.append("source_epoch_transition")
        if observation.capture_age_ms > 5_000:
            reasons.append("stale_capture")
            state = HealthState.STALE
        elif previous and previous.state in {HealthState.STALE, HealthState.FAILED}:
            reasons.append("source_recovered")
            state = HealthState.HEALTHY
        if any(abs(value) > 1_000_000 for value in observation.values.values()):
            raise ValueError("implausible numeric value")
        buffer = self._buffers.setdefault(observation.source_id, BoundedRingBuffer(self._capacity))
        buffer.append(observation)
        if buffer.dropped:
            reasons.append("ring_buffer_overwrite")
            if state == HealthState.HEALTHY:
                state = HealthState.DEGRADED
        health = SourceHealth(
            source_id=observation.source_id,
            state=state,
            boot_id=observation.boot_id,
            clock_epoch=observation.clock_epoch,
            last_sequence=observation.sequence,
            last_observed_at=observation.observed_at,
            event_time_watermark=(
                previous.event_time_watermark
                if previous is not None and previous.event_time_watermark is not None and observation.observed_at < previous.event_time_watermark
                else observation.observed_at
            ),
            clock_uncertainty_ms=observation.clock_uncertainty_ms,
            reason_codes=tuple(sorted(set(reasons))),
        )
        self._cursor_store.upsert(health)
        self._health[observation.source_id] = health
        return observation

    def health(self) -> tuple[SourceHealth, ...]:
        return tuple(sorted(self._health.values(), key=lambda item: item.source_id))

    def mark_stale(self, now: datetime | None = None, threshold_seconds: int = 30) -> None:
        now = now or datetime.now(timezone.utc)
        for source_id, health in list(self._health.items()):
            if health.last_observed_at and (now - health.last_observed_at).total_seconds() > threshold_seconds:
                updated = health.model_copy(
                    update={"state": HealthState.STALE, "reason_codes": tuple(sorted(set(health.reason_codes + ("timeout",))))}
                )
                self._health[source_id] = updated
                self._cursor_store.upsert(updated, recorded_at=now)

    def mark_failed(self, source_id: str, reason: str, now: datetime | None = None) -> None:
        if source_id not in self._health:
            raise KeyError(source_id)
        now = now or datetime.now(timezone.utc)
        current = self._health[source_id]
        updated = current.model_copy(
            update={
                "state": HealthState.FAILED,
                "last_observed_at": current.last_observed_at,
                "event_time_watermark": current.event_time_watermark,
                "reason_codes": tuple(sorted(set(current.reason_codes + (reason,)))),
            }
        )
        self._health[source_id] = updated
        self._cursor_store.upsert(updated, recorded_at=now)

    def health_events(self) -> tuple[Any, ...]:
        return self._cursor_store.events()
