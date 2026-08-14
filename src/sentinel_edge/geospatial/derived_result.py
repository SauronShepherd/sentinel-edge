"""Derived spatial results retain transform and grid provenance."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DerivedSpatialResult:
    value: Any
    operation: str
    grid_identities: tuple[str, ...]
    accuracy_m: float

    def __post_init__(self) -> None:
        if not self.operation.strip() or not self.grid_identities or any(not item.strip() for item in self.grid_identities):
            raise ValueError("derived spatial result requires operation and grid identities")
        if self.accuracy_m < 0:
            raise ValueError("derived spatial accuracy cannot be negative")

    def provenance(self) -> dict[str, Any]:
        return {"operation": self.operation, "grid_identities": list(self.grid_identities), "accuracy_m": self.accuracy_m}
