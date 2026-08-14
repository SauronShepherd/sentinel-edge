"""Explicit replay-verification classes and deterministic reports."""

from __future__ import annotations

import math
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from sentinel_edge.security import canonical_json_bytes, sha256_bytes


class ReplayCheckClass(StrEnum):
    BYTE_EXACT = "byte_exact"
    NUMERIC_TOLERANCE = "numeric_tolerance"
    SEMANTIC = "semantic"


class ReplayVerificationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    check_class: ReplayCheckClass
    passed: bool
    absolute_tolerance: float = Field(ge=0.0)
    relative_tolerance: float = Field(ge=0.0)
    expected_sha256: str
    actual_sha256: str
    mismatch_paths: tuple[str, ...] = ()
    semantic_fields: tuple[str, ...] = ()


def _digest(value: Any) -> str:
    if isinstance(value, bytes):
        payload = value
    else:
        payload = canonical_json_bytes(value)
    return sha256_bytes(payload)


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _numeric_mismatches(expected: Any, actual: Any, path: str, absolute: float, relative: float, out: list[str]) -> None:
    if _number(expected) and _number(actual):
        difference = abs(float(expected) - float(actual))
        bound = absolute + relative * max(abs(float(expected)), abs(float(actual)))
        if not math.isfinite(difference) or difference > bound:
            out.append(path or "$")
        return
    if type(expected) is not type(actual):
        out.append(path or "$")
        return
    if isinstance(expected, dict):
        keys = sorted(set(expected) | set(actual))
        for key in keys:
            child = f"{path}.{key}" if path else str(key)
            if key not in expected or key not in actual:
                out.append(child)
            else:
                _numeric_mismatches(expected[key], actual[key], child, absolute, relative, out)
        return
    if isinstance(expected, (list, tuple)):
        if len(expected) != len(actual):
            out.append(path or "$")
            return
        for index, (left, right) in enumerate(zip(expected, actual)):
            _numeric_mismatches(left, right, f"{path}[{index}]", absolute, relative, out)
        return
    if expected != actual:
        out.append(path or "$")


def verify_replay(
    expected: Any,
    actual: Any,
    *,
    check_class: ReplayCheckClass,
    absolute_tolerance: float = 0.0,
    relative_tolerance: float = 0.0,
    semantic_fields: tuple[str, ...] = (),
) -> ReplayVerificationReport:
    """Compare replay output without silently upgrading a weaker check class."""
    if absolute_tolerance < 0 or relative_tolerance < 0:
        raise ValueError("replay tolerances must be non-negative")
    mismatches: list[str] = []
    if check_class is ReplayCheckClass.BYTE_EXACT:
        if isinstance(expected, bytes) or isinstance(actual, bytes):
            if expected != actual:
                mismatches.append("$")
        elif canonical_json_bytes(expected) != canonical_json_bytes(actual):
            mismatches.append("$")
    elif check_class is ReplayCheckClass.NUMERIC_TOLERANCE:
        _numeric_mismatches(expected, actual, "", absolute_tolerance, relative_tolerance, mismatches)
    else:
        if not semantic_fields:
            raise ValueError("semantic replay checks require semantic_fields")
        if not isinstance(expected, dict) or not isinstance(actual, dict):
            raise ValueError("semantic replay checks require mapping values")
        for field in semantic_fields:
            if field not in expected or field not in actual or expected[field] != actual[field]:
                mismatches.append(field)
    return ReplayVerificationReport(
        check_class=check_class,
        passed=not mismatches,
        absolute_tolerance=absolute_tolerance,
        relative_tolerance=relative_tolerance,
        expected_sha256=_digest(expected),
        actual_sha256=_digest(actual),
        mismatch_paths=tuple(sorted(set(mismatches))),
        semantic_fields=tuple(semantic_fields),
    )
