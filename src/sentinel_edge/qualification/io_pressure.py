"""I/O pressure and durability-tail diagnostic snapshot."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IoPressureSnapshot:
    io_psi_avg10: float | None
    dirty_writeback_seconds: float | None
    fsync_tail_seconds: float | None
    wal_checkpoint_tail_seconds: float | None
    evidence_encoding_tail_seconds: float | None
    cpu_pressure: float | None
    memory_pressure: float | None

    def __post_init__(self) -> None:
        for value in (self.io_psi_avg10, self.dirty_writeback_seconds, self.fsync_tail_seconds, self.wal_checkpoint_tail_seconds, self.evidence_encoding_tail_seconds, self.cpu_pressure, self.memory_pressure):
            if value is not None and value < 0:
                raise ValueError("pressure and latency metrics cannot be negative")

    def classify(self) -> str:
        if self.io_psi_avg10 is None:
            return "io_metrics_unavailable"
        if self.io_psi_avg10 > 0 and (self.cpu_pressure or 0) < self.io_psi_avg10 and (self.memory_pressure or 0) < self.io_psi_avg10:
            return "io_stall_pressure"
        return "cpu_or_memory_pressure"

    def as_snapshot(self) -> dict[str, float | str | None]:
        return {"io_psi_avg10": self.io_psi_avg10, "dirty_writeback_seconds": self.dirty_writeback_seconds, "fsync_tail_seconds": self.fsync_tail_seconds, "wal_checkpoint_tail_seconds": self.wal_checkpoint_tail_seconds, "evidence_encoding_tail_seconds": self.evidence_encoding_tail_seconds, "cpu_pressure": self.cpu_pressure, "memory_pressure": self.memory_pressure, "classification": self.classify()}
