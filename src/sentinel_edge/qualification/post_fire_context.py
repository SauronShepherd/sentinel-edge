"""Bounded post-fire context: cadence/review only, never hazard-state evidence."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class PostFireContext:
    fire_id: str
    fire_area: frozenset[str]
    affected_area: frozenset[str]
    observed_at: datetime
    now: datetime
    maximum_age: timedelta = timedelta(days=30)


@dataclass(frozen=True)
class PostFireDecision:
    cadence_multiplier: float
    review_required: bool
    hazard_state_influence: bool
    reason_codes: tuple[str, ...]


def evaluate_post_fire_context(context: PostFireContext) -> PostFireDecision:
    if context.now.tzinfo is None or context.observed_at.tzinfo is None:
        raise ValueError("post-fire timestamps must be timezone-aware")
    if not context.fire_id.strip():
        raise ValueError("fire_id is required")
    age = context.now - context.observed_at
    if age < timedelta(0) or age > context.maximum_age:
        return PostFireDecision(1.0, True, False, ("post_fire_context_expired", "review_required"))
    if not context.fire_area.intersection(context.affected_area):
        return PostFireDecision(1.0, False, False, ("post_fire_spatial_non_overlap",))
    return PostFireDecision(2.0, True, False, ("post_fire_overlap_fresh", "cadence_only", "review_required"))
