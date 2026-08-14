"""Map geospatial runtime changes to affected tests and claims."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeospatialChangeImpact:
    change_id: str
    changed_component: str
    affected_operations: tuple[str, ...]
    affected_tests: tuple[str, ...]
    affected_claims: tuple[str, ...]
    rerun_required: bool = True

    def __post_init__(self) -> None:
        if not self.change_id.strip() or not self.changed_component.strip():
            raise ValueError("geospatial change identity is required")
        if self.rerun_required and (not self.affected_tests or not self.affected_operations):
            raise ValueError("material geospatial changes require operations and tests")

    def claim_impact(self) -> dict[str, object]:
        return {"change_id": self.change_id, "component": self.changed_component, "operations": list(self.affected_operations), "tests": list(self.affected_tests), "claims": list(self.affected_claims), "rerun_required": self.rerun_required}
