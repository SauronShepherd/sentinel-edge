"""Explicit declarations for material CRS transformations."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TransformDeclaration:
    source_crs: str
    target_crs: str
    operation: str
    area_of_use: str
    coordinate_epoch: float | None
    accuracy_m: float

    def __post_init__(self) -> None:
        if any(not value.strip() for value in (self.source_crs, self.target_crs, self.operation, self.area_of_use)):
            raise ValueError("CRS transform declaration is incomplete")
        if self.accuracy_m < 0:
            raise ValueError("transform accuracy cannot be negative")


def validate_transform_declaration(declaration: TransformDeclaration) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if declaration.operation.lower().startswith("ballpark"):
        reasons.append("ballpark_operation_not_allowed")
    if declaration.coordinate_epoch is None:
        reasons.append("coordinate_epoch_unresolved")
    return not reasons, tuple(reasons)


def validate_required_grids(*, selected_operation: str, selected_grids: frozenset[str], required_grids: frozenset[str]) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if selected_operation.lower().startswith(("ballpark", "identity", "no-grid")):
        reasons.append("unexpected_fallback_operation")
    for grid in sorted(required_grids - selected_grids):
        reasons.append(f"required_grid_missing:{grid}")
    return not reasons, tuple(reasons)
