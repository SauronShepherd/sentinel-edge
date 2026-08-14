"""Small firmware-portable deterministic trigger kernel.

The kernel consumes fixed-size IMU windows and returns a compact decision.  It
has no Linux, NumPy, model-runtime, allocation-heavy, or wall-clock dependency,
so the same arithmetic can be implemented by a sensor-plane MCU and replayed
by the development emulator.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from math import sqrt
from time import monotonic_ns

from pydantic import BaseModel, ConfigDict, Field


class TriggerDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    triggered: bool
    peak_magnitude: float = Field(ge=0.0)
    threshold: float = Field(ge=0.0)
    sample_count: int = Field(ge=0)
    reason: str


class TriggerPathMeasurement(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sample_count: int = Field(ge=0)
    repetitions: int = Field(gt=0)
    triggered_count: int = Field(ge=0)
    worst_elapsed_ns: int = Field(ge=0)
    deterministic: bool


def evaluate_external_trigger(
    samples: Sequence[tuple[float, float, float]],
    *,
    threshold: float = 1.5,
) -> TriggerDecision:
    """Evaluate a fixed IMU window using bounded scalar arithmetic."""
    if threshold < 0.0:
        raise ValueError("trigger threshold must be non-negative")
    peak = 0.0
    for x, y, z in samples:
        magnitude = sqrt(float(x) * float(x) + float(y) * float(y) + float(z) * float(z))
        if magnitude > peak:
            peak = magnitude
    return TriggerDecision(
        triggered=peak >= threshold,
        peak_magnitude=peak,
        threshold=threshold,
        sample_count=len(samples),
        reason="threshold_crossed" if peak >= threshold else "below_threshold",
    )


def measure_trigger_path(
    samples: Iterable[tuple[float, float, float]],
    *,
    threshold: float = 1.5,
    repetitions: int = 100,
) -> TriggerPathMeasurement:
    """Measure bounded development execution without claiming target hardware."""
    window = tuple(samples)
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    first = evaluate_external_trigger(window, threshold=threshold)
    triggered_count = 0
    worst = 0
    for _ in range(repetitions):
        start = monotonic_ns()
        decision = evaluate_external_trigger(window, threshold=threshold)
        worst = max(worst, monotonic_ns() - start)
        triggered_count += int(decision.triggered)
        if decision != first:
            raise RuntimeError("external trigger path is not deterministic")
    return TriggerPathMeasurement(
        sample_count=len(window), repetitions=repetitions,
        triggered_count=triggered_count, worst_elapsed_ns=worst, deterministic=True,
    )
