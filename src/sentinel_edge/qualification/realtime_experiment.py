"""Time-boxed privileged scheduling experiments kept separate from default proof."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RealtimeExperimentResult:
    experiment_id: str
    elapsed_seconds: float
    watchdog_expired: bool
    replaces_default_proof: bool = False

    def __post_init__(self) -> None:
        if not self.experiment_id.strip() or self.elapsed_seconds < 0:
            raise ValueError("experiment identity and non-negative elapsed time are required")
        if self.replaces_default_proof:
            raise ValueError("privileged experiment cannot replace default proof")


def timebox_realtime_experiment(experiment_id: str, *, elapsed_seconds: float, timeout_seconds: float) -> RealtimeExperimentResult:
    if timeout_seconds <= 0 or elapsed_seconds < 0:
        raise ValueError("experiment and timeout bounds must be valid")
    return RealtimeExperimentResult(experiment_id, min(elapsed_seconds, timeout_seconds), elapsed_seconds > timeout_seconds)
