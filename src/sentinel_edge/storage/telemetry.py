from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sentinel_edge.storage.artifact_governance import ArtifactPolicy, ArtifactScope
from sentinel_edge.storage.artifacts import ArtifactRef, ContentAddressedArtifactStore


@dataclass(frozen=True)
class TelemetryWriteReport:
    observations: int
    batches: int
    logical_bytes: int
    physical_bytes: int
    write_amplification_proxy: float
    estimated_bytes_per_day: float
    retention_days: int
    within_budget: bool


class TelemetryBatchWriter:
    """Batches noncritical telemetry so high-rate sources do not cause per-sample writes."""

    def __init__(
        self,
        store: ContentAddressedArtifactStore,
        *,
        batch_items: int = 100,
        flush_interval_seconds: int = 10,
        bytes_per_day_budget: int = 64 * 1024 * 1024,
        retention_days: int = 7,
    ) -> None:
        if min(batch_items, flush_interval_seconds, bytes_per_day_budget, retention_days) <= 0:
            raise ValueError("telemetry budgets must be positive")
        self.store = store
        self.batch_items = batch_items
        self.flush_interval = timedelta(seconds=flush_interval_seconds)
        self.bytes_per_day_budget = bytes_per_day_budget
        self.retention_days = retention_days
        self._buffer: list[dict[str, Any]] = []
        self._opened_at: datetime | None = None
        self._observations = 0
        self._logical_bytes = 0
        self._physical_bytes = 0
        self._batches = 0
        self._first_observed_at: datetime | None = None
        self._last_observed_at: datetime | None = None
        self._refs: list[ArtifactRef] = []

    def append(self, record: dict[str, Any], *, observed_at: datetime | None = None) -> ArtifactRef | None:
        observed_at = observed_at or datetime.now(timezone.utc)
        encoded = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if self._opened_at is None:
            self._opened_at = observed_at
        self._first_observed_at = self._first_observed_at or observed_at
        self._last_observed_at = observed_at
        self._buffer.append(record)
        self._observations += 1
        self._logical_bytes += len(encoded)
        if len(self._buffer) >= self.batch_items or observed_at - self._opened_at >= self.flush_interval:
            return self.flush()
        return None

    def flush(self) -> ArtifactRef | None:
        if not self._buffer:
            return None
        payload = b"\n".join(
            json.dumps(item, sort_keys=True, separators=(",", ":")).encode("utf-8")
            for item in self._buffer
        ) + b"\n"
        ref = self.store.put_bytes(
            payload, media_type="application/x-ndjson", critical=False,
            policy=ArtifactPolicy.telemetry_batch(), scope=ArtifactScope(source_id="node-telemetry"),
        )
        self._refs.append(ref)
        self._physical_bytes += ref.bytes
        self._batches += 1
        self._buffer.clear()
        self._opened_at = None
        return ref

    def report(self) -> TelemetryWriteReport:
        duration_seconds = 0.0
        if self._first_observed_at and self._last_observed_at:
            duration_seconds = max(1.0, (self._last_observed_at - self._first_observed_at).total_seconds())
        estimated_per_day = self._physical_bytes * (86400.0 / duration_seconds) if duration_seconds else float(self._physical_bytes)
        amplification = self._physical_bytes / max(1, self._logical_bytes)
        return TelemetryWriteReport(
            observations=self._observations,
            batches=self._batches,
            logical_bytes=self._logical_bytes,
            physical_bytes=self._physical_bytes,
            write_amplification_proxy=amplification,
            estimated_bytes_per_day=estimated_per_day,
            retention_days=self.retention_days,
            within_budget=estimated_per_day <= self.bytes_per_day_budget,
        )

    @property
    def artifact_refs(self) -> tuple[ArtifactRef, ...]:
        return tuple(self._refs)
