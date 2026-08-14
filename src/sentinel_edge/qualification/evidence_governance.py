"""Typed evidence for subgroup quality, bias, and licence separation."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class LicenceSubject(StrEnum):
    ARTICLE = "article"
    DATASET = "dataset"
    CODE = "code"
    MODEL_WEIGHTS = "model_weights"
    UPSTREAM_IMAGERY = "upstream_imagery"


@dataclass(frozen=True)
class LicenceRecord:
    subject: LicenceSubject
    licence_id: str
    terms_url: str
    redistribution_allowed: bool
    deployment_allowed: bool

    def __post_init__(self) -> None:
        if not self.licence_id.strip() or not self.terms_url.strip():
            raise ValueError("licence identity and terms URL are required")


@dataclass(frozen=True)
class BiasRecord:
    geography: str
    source_selection: str
    reporting: str
    missing_observation: str

    def __post_init__(self) -> None:
        if any(not value.strip() for value in self.__dict__.values()):
            raise ValueError("all bias dimensions must be documented")


@dataclass(frozen=True)
class SubgroupMetric:
    subgroup: str
    sample_count: int
    recall: float
    false_alarm_rate: float
    calibration_error: float


def validate_subgroup_metrics(metrics: tuple[SubgroupMetric, ...], *, critical_subgroups: frozenset[str]) -> tuple[bool, tuple[str, ...]]:
    if not metrics:
        return False, ("subgroup_metrics_missing",)
    by_name = {item.subgroup: item for item in metrics}
    missing = sorted(critical_subgroups - by_name.keys())
    if missing:
        return False, tuple(f"critical_subgroup_missing:{name}" for name in missing)
    failed = sorted(item.subgroup for item in metrics if item.sample_count <= 0 or not 0 <= item.recall <= 1 or not 0 <= item.false_alarm_rate <= 1 or item.recall < 0.5)
    if failed:
        return False, tuple(f"critical_subgroup_failed:{name}" for name in failed)
    return True, ("all_declared_subgroups_passed",)
