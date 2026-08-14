"""Conservative, dimension-bound drift surveillance decisions."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DriftKind(StrEnum):
    MISSINGNESS = "missingness_quality"
    SENSOR = "sensor_calibration"
    UPSTREAM = "upstream_version"
    PREVALENCE = "prevalence_shift"


class DriftAction(StrEnum):
    PRESERVE = "preserve"
    WEAKEN = "weaken"
    SHADOW = "shadow"
    REVIEW_REQUIRED = "review_required"
    BLOCK = "block"


@dataclass(frozen=True)
class DriftBaseline:
    hazard: str
    site: str
    sensor_chain: str
    model_profile: str
    source_lineage: str
    season: str
    operator: str

    def __post_init__(self) -> None:
        if any(not value.strip() for value in self.__dict__.values()):
            raise ValueError("drift baseline dimensions must not be blank")


@dataclass(frozen=True)
class DriftObservation:
    baseline: DriftBaseline
    kind: DriftKind
    sample_count: int
    effective_duration_seconds: float
    uncertainty: float
    persistence_windows: int
    evidence: bool = True


@dataclass(frozen=True)
class DriftDecision:
    action: DriftAction
    kind: DriftKind
    reason_codes: tuple[str, ...]
    automatic_retraining_allowed: bool = False
    automatic_threshold_change_allowed: bool = False


def evaluate_drift(observation: DriftObservation, *, minimum_samples: int = 30, minimum_duration_seconds: float = 300.0, minimum_persistence_windows: int = 3) -> DriftDecision:
    if observation.sample_count < minimum_samples or observation.effective_duration_seconds < minimum_duration_seconds or observation.persistence_windows < minimum_persistence_windows:
        return DriftDecision(DriftAction.PRESERVE, observation.kind, ("insufficient_persistent_evidence",))
    if not observation.evidence:
        return DriftDecision(DriftAction.REVIEW_REQUIRED, observation.kind, ("drift_cause_unproven",))
    action = DriftAction.WEAKEN if observation.kind in {DriftKind.MISSINGNESS, DriftKind.SENSOR} else DriftAction.REVIEW_REQUIRED
    return DriftDecision(action, observation.kind, (f"classified:{observation.kind.value}", "incident_confidence_not_strengthened"))
