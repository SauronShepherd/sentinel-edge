"""Path policy for optional generated prose."""
from __future__ import annotations

from enum import StrEnum


class ExecutionPath(StrEnum):
    CRITICAL_STATE = "critical_state"
    JUDGE = "judge"
    BENCHMARK = "benchmark"
    OPERATOR_REVIEW = "operator_review"


def generated_prose_allowed(path: ExecutionPath) -> bool:
    return path is ExecutionPath.OPERATOR_REVIEW


def require_deterministic_wording(path: ExecutionPath, *, generated: bool) -> None:
    if generated and not generated_prose_allowed(path):
        raise PermissionError("generated prose is disabled on critical, judge, and benchmark paths")
