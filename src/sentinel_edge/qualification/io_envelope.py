"""Benchmark-host I/O pressure and persistence-tail envelope."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IoQualificationEnvelope:
    max_io_psi_avg10: float
    max_fsync_tail_seconds: float
    max_wal_checkpoint_tail_seconds: float
    max_evidence_encoding_tail_seconds: float

    def __post_init__(self) -> None:
        if min(self.max_io_psi_avg10, self.max_fsync_tail_seconds, self.max_wal_checkpoint_tail_seconds, self.max_evidence_encoding_tail_seconds) < 0:
            raise ValueError("I/O envelope limits cannot be negative")

    def evaluate(self, *, io_psi_avg10: float, fsync_tail_seconds: float, wal_checkpoint_tail_seconds: float, evidence_encoding_tail_seconds: float) -> dict[str, object]:
        values = (io_psi_avg10, fsync_tail_seconds, wal_checkpoint_tail_seconds, evidence_encoding_tail_seconds)
        if min(values) < 0:
            raise ValueError("I/O observations cannot be negative")
        within = io_psi_avg10 <= self.max_io_psi_avg10 and fsync_tail_seconds <= self.max_fsync_tail_seconds and wal_checkpoint_tail_seconds <= self.max_wal_checkpoint_tail_seconds and evidence_encoding_tail_seconds <= self.max_evidence_encoding_tail_seconds
        return {"within_envelope": within, "headline_claim_allowed": within, "label": "qualified" if within else "io_out_of_envelope"}
