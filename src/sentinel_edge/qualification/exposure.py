"""Potential-exposure estimates kept independent from hazard verification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class VerificationState(StrEnum):
    UNVERIFIED = "unverified"
    SUSPECTED = "suspected"
    CONFIRMED = "confirmed"


@dataclass(frozen=True)
class ExposureEstimate:
    estimated_population: int = 0
    estimated_buildings: int = 0
    source_version: str = "unknown"

    def __post_init__(self) -> None:
        if self.estimated_population < 0 or self.estimated_buildings < 0:
            raise ValueError("exposure estimates cannot be negative")

    def wording(self) -> str:
        return f"estimated potential exposure: approximately {self.estimated_population} people and {self.estimated_buildings} buildings"


@dataclass(frozen=True)
class HazardVerification:
    state: VerificationState
    confidence: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("verification confidence must be between zero and one")


@dataclass(frozen=True)
class ReviewPriorityRule:
    version: str = "exposure-priority-v1"
    high_population_threshold: int = 1000
    high_building_threshold: int = 100
    priority_duration_seconds: int = 900
    monitoring_cadence_seconds: int = 60

    def priority(self, exposure: ExposureEstimate) -> tuple[str, str]:
        high = exposure.estimated_population >= self.high_population_threshold or exposure.estimated_buildings >= self.high_building_threshold
        return ("high", "potential_exposure_threshold") if high else ("normal", "baseline")


def combine_exposure_and_verification(exposure: ExposureEstimate, verification: HazardVerification, rule: ReviewPriorityRule | None = None) -> dict[str, object]:
    """Return a display contract; exposure never upgrades verification state."""
    rule = rule or ReviewPriorityRule()
    priority, reason = rule.priority(exposure)
    return {
        "exposure": exposure,
        "verification": verification,
        "review_priority": priority,
        "priority_reason": reason,
        "priority_rule_version": rule.version,
        "priority_duration_seconds": rule.priority_duration_seconds,
        "monitoring_cadence_seconds": rule.monitoring_cadence_seconds,
    }
