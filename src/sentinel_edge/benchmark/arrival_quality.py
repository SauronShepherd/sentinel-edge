"""Load-generator arrival jitter and instrumentation-overhead qualification."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArrivalQualityReport:
    qualified_jitter_seconds: float
    observed_jitter_seconds: float
    instrumentation_overhead_fraction: float
    overhead_limit_fraction: float

    @property
    def valid(self) -> bool:
        return self.observed_jitter_seconds <= self.qualified_jitter_seconds and self.instrumentation_overhead_fraction <= self.overhead_limit_fraction

    def label(self) -> str:
        return "qualified" if self.valid else "invalidated_or_labeled"

    def __post_init__(self) -> None:
        if min(self.qualified_jitter_seconds, self.observed_jitter_seconds, self.instrumentation_overhead_fraction, self.overhead_limit_fraction) < 0:
            raise ValueError("arrival and overhead metrics cannot be negative")
