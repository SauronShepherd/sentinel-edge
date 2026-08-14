"""Reconciled simultaneous-event I/O pressure transcript."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IoPressureTranscript:
    queue_age_seconds: float
    pressure: bool
    shedding: tuple[str, ...]
    missed_evidence: tuple[str, ...]
    deadline_outcomes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.queue_age_seconds < 0:
            raise ValueError("queue age cannot be negative")
        if not self.deadline_outcomes:
            raise ValueError("deadline outcomes are required")

    def reconciled(self) -> bool:
        return self.pressure or (not self.shedding and not self.missed_evidence)
