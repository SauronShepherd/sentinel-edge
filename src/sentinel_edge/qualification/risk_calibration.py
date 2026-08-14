"""Selective-risk calibration report that preserves critical subgroup failures."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskCalibrationReport:
    abstention_rate: float
    recall: float
    false_alert_rate: float
    entropy_shift: float
    subgroup_metrics: dict[str, dict[str, float]]

    def __post_init__(self) -> None:
        for value in (self.abstention_rate, self.recall, self.false_alert_rate, self.entropy_shift):
            if value < 0:
                raise ValueError("calibration metrics cannot be negative")

    def failures(self) -> tuple[str, ...]:
        failures = []
        if self.abstention_rate <= 0:
            failures.append("abstention_not_observed")
        if self.recall < 1.0:
            failures.append("recall_incomplete")
        if self.false_alert_rate > 0:
            failures.append("false_alerts_present")
        for subgroup, metrics in sorted(self.subgroup_metrics.items()):
            if metrics.get("recall", 1.0) < 1.0:
                failures.append(f"subgroup_recall_failed:{subgroup}")
            if metrics.get("false_alert_rate", 0.0) > 0:
                failures.append(f"subgroup_false_alerts:{subgroup}")
        return tuple(failures)
