"""Offline FIRMS lineage and availability semantics."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FirmsProcessingClass(StrEnum):
    RT = "RT"
    URT = "URT"
    NRT = "NRT"
    STANDARD = "standard-processing"


@dataclass(frozen=True)
class FirmsObservation:
    observation_id: str
    sensor: str
    product: str
    processing_class: FirmsProcessingClass
    correlation_family: str
    fire_detected: bool

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.observation_id, self.sensor, self.product, self.correlation_family)):
            raise ValueError("FIRMS lineage fields are required")


@dataclass(frozen=True)
class FirmsAvailability:
    date: str
    available: bool
    missing_reason: str | None = None

    def completeness_factor(self) -> float:
        return 1.0 if self.available else 0.0


def assess_firms_completeness(states: tuple[FirmsAvailability, ...]) -> tuple[float, bool]:
    if not states:
        raise ValueError("at least one FIRMS availability state is required")
    return sum(item.completeness_factor() for item in states) / len(states), any(not item.available for item in states)
