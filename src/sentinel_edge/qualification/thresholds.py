"""Declared decision margins for unstable threshold regions."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable

from sentinel_edge.domain.models import IncidentState


@dataclass(frozen=True)
class ThresholdDecision:
    state: IncidentState
    abstained: bool
    reason_code: str | None = None


def decide_with_margin(
    score: float,
    *,
    thresholds: Iterable[tuple[float, IncidentState]],
    margin: float = 0.03,
) -> ThresholdDecision:
    """Return a conservative state when a score lies near a declared boundary.

    The margin is part of the decision contract: a score within it cannot silently
    flip a high-impact state because of insignificant numeric or sensor variation.
    """
    if not 0.0 <= score <= 1.0:
        raise ValueError("score must be within [0,1]")
    if margin < 0.0:
        raise ValueError("threshold margin must be non-negative")
    ordered = sorted(thresholds, key=lambda item: item[0])
    if any(not 0.0 <= threshold <= 1.0 for threshold, _ in ordered):
        raise ValueError("thresholds must be within [0,1]")
    if any(left[0] >= right[0] for left, right in zip(ordered, ordered[1:])):
        raise ValueError("thresholds must be strictly increasing")
    for threshold, _ in ordered:
        if abs(score - threshold) <= margin:
            return ThresholdDecision(
                state=IncidentState.WATCH,
                abstained=True,
                reason_code="decision_threshold_margin_abstention",
            )
    state = IncidentState.NORMAL
    for threshold, candidate in ordered:
        if score >= threshold:
            state = candidate
    return ThresholdDecision(state=state, abstained=False)
