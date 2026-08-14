"""Deterministic earthquake hard-negative execution and reporting."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field



class HardNegativeKind(StrEnum):
    HANDLING = "handling"
    FOOTSTEPS = "footsteps"
    TRAFFIC = "traffic"


class HardNegativeCase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str
    kind: HardNegativeKind
    dynamic_acceleration_g: float
    classifier_label: str
    expected_nonseismic: bool
    passed: bool


class HardNegativeReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    profile_id: str
    cases: tuple[HardNegativeCase, ...]
    passed: bool
    failure_count: int = Field(ge=0)
    classification: str = "simulated"


DEFAULT_HARD_NEGATIVE_WINDOWS: tuple[tuple[HardNegativeKind, str, float], ...] = (
    (HardNegativeKind.HANDLING, "handling-low", 0.08),
    (HardNegativeKind.FOOTSTEPS, "footsteps-low", 0.14),
    (HardNegativeKind.TRAFFIC, "traffic-low", 0.18),
)


def build_hard_negative_report(
    windows: tuple[tuple[HardNegativeKind, str, float], ...] = DEFAULT_HARD_NEGATIVE_WINDOWS,
) -> HardNegativeReport:
    from sentinel_edge.hazards.earthquake import EarthquakeAdapter

    adapter = EarthquakeAdapter()
    cases = tuple(
        HardNegativeCase(
            case_id=case_id,
            kind=kind,
            dynamic_acceleration_g=dynamic,
            classifier_label=adapter.classify_int8(dynamic),
            expected_nonseismic=True,
            passed=adapter.classify_int8(dynamic) == "nonseismic",
        )
        for kind, case_id, dynamic in windows
    )
    failures = sum(not case.passed for case in cases)
    return HardNegativeReport(
        profile_id=adapter.adapter_id,
        cases=cases,
        passed=failures == 0,
        failure_count=failures,
    )
