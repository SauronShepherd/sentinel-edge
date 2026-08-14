"""Deterministic known-answer checks for transform classes."""
from __future__ import annotations

from dataclasses import dataclass
from math import isclose


@dataclass(frozen=True)
class TransformKnownAnswer:
    name: str
    expected: tuple[float, ...]
    tolerance: float
    require_non_identity: bool = False


def verify_known_answer(answer: TransformKnownAnswer, observed: tuple[float, ...], *, input_values: tuple[float, ...]) -> tuple[bool, tuple[str, ...]]:
    if answer.tolerance < 0 or len(observed) != len(answer.expected) or len(input_values) != len(observed):
        return False, ("known_answer_shape_or_tolerance_invalid",)
    reasons: list[str] = []
    if any(not isclose(actual, expected, abs_tol=answer.tolerance, rel_tol=0.0) for actual, expected in zip(observed, answer.expected)):
        reasons.append("known_answer_outside_tolerance")
    if answer.require_non_identity and observed == input_values:
        reasons.append("unexpected_identity_transform")
    return not reasons, tuple(reasons)
