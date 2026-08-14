"""Compact release-status snapshot for scope convergence."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReleaseStatusSnapshot:
    h0_total: int
    h0_closed: int
    h0_delta: int
    critical_path: tuple[str, ...]
    exceptions: tuple[str, ...]
    optional_work_budget: int

    def __post_init__(self) -> None:
        if min(self.h0_total, self.h0_closed, self.optional_work_budget) < 0 or self.h0_closed > self.h0_total:
            raise ValueError("release status counts are invalid")
        if self.h0_delta != self.h0_total - self.h0_closed:
            raise ValueError("H0 delta must equal total minus closed")
        if not self.critical_path:
            raise ValueError("critical path must be declared")

    def as_dict(self) -> dict[str, object]:
        return {"h0_total": self.h0_total, "h0_closed": self.h0_closed, "h0_delta": self.h0_delta, "critical_path": list(self.critical_path), "exceptions": list(self.exceptions), "optional_work_budget": self.optional_work_budget}
