from __future__ import annotations

import math
import time
from dataclasses import dataclass
from pathlib import Path
import re


_REMOVED_ARMNN = re.compile((b"arm" + b"nn") + rb"|arm[_ -]?nn", re.IGNORECASE)


def scan_removed_armnn(root: str | Path) -> dict[str, object]:
    """Scan executable/configuration material for the removed ArmNN provider."""
    base = Path(root)
    findings: list[str] = []
    ignored = {"docs", "registries", ".git", ".venv", "qualification"}
    for path in sorted(base.rglob("*")):
        if not path.is_file() or any(part in ignored for part in path.parts):
            continue
        if path.suffix.lower() not in {".py", ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg", ".ts", ".js"}:
            continue
        if _REMOVED_ARMNN.search(path.read_bytes()):
            findings.append(path.relative_to(base).as_posix())
    return {"forbidden_provider": "Arm" + "NN", "findings": findings, "valid": not findings}
from typing import Any, Callable, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sentinel_edge.domain.models import CapabilityState
from sentinel_edge.security import canonical_json_bytes, sha256_bytes


class RuntimeSession(Protocol):
    def run(self, inputs: dict[str, Any]) -> dict[str, Any]: ...


class KnownAnswerCase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str
    branch_id: str
    inputs: dict[str, Any]
    expected_outputs: dict[str, Any]
    tolerance: float = Field(default=0.0, ge=0.0)

    @field_validator("case_id", "branch_id")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("known-answer identifiers must not be blank")
        return value


class KnownAnswerSuite(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    suite_id: str
    model_graph_sha256: str
    runtime_profile_sha256: str
    required_branches: tuple[str, ...]
    cases: tuple[KnownAnswerCase, ...]
    session_initialization_repetitions: int = Field(default=2, ge=2, le=32)


def _matches(actual: Any, expected: Any, tolerance: float) -> bool:
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return math.isclose(float(actual), float(expected), rel_tol=tolerance, abs_tol=tolerance)
    if isinstance(expected, list) and isinstance(actual, list) and len(actual) == len(expected):
        return all(_matches(a, e, tolerance) for a, e in zip(actual, expected))
    if isinstance(expected, dict) and isinstance(actual, dict) and set(actual) == set(expected):
        return all(_matches(actual[key], expected[key], tolerance) for key in expected)
    return actual == expected


def run_known_answer_suite(
    suite: KnownAnswerSuite | dict[str, Any],
    session_factory: Callable[[], RuntimeSession],
    *,
    target_host_qualified: bool,
    target_runtime_qualified: bool,
) -> dict[str, Any]:
    item = suite if isinstance(suite, KnownAnswerSuite) else KnownAnswerSuite.model_validate(suite)
    failures: list[str] = []
    initialization_ms: list[float] = []
    sessions: list[RuntimeSession] = []
    for index in range(item.session_initialization_repetitions):
        started = time.perf_counter_ns()
        try:
            sessions.append(session_factory())
        except Exception as exc:  # fail closed before service
            failures.append(f"session_initialization_failed:{index}:{type(exc).__name__}")
            break
        initialization_ms.append((time.perf_counter_ns() - started) / 1_000_000)
    case_results: list[dict[str, Any]] = []
    covered: set[str] = set()
    if sessions:
        session = sessions[0]
        for case in item.cases:
            case_failures: list[str] = []
            try:
                actual = session.run(case.inputs)
            except Exception as exc:
                actual = {}
                case_failures.append(f"runtime_execution_failed:{type(exc).__name__}")
            if set(actual) != set(case.expected_outputs):
                case_failures.append("output_shape_or_name_mismatch")
            elif not _matches(actual, case.expected_outputs, case.tolerance):
                case_failures.append("known_answer_mismatch")
            if not case_failures:
                covered.add(case.branch_id)
            failures.extend(f"case:{case.case_id}:{value}" for value in case_failures)
            case_results.append({
                "case_id": case.case_id,
                "branch_id": case.branch_id,
                "passed": not case_failures,
                "failures": case_failures,
                "actual_output_sha256": sha256_bytes(canonical_json_bytes(actual)),
            })
    missing = sorted(set(item.required_branches) - covered)
    failures.extend(f"required_branch_not_covered:{branch}" for branch in missing)
    development_passed = not failures
    target_qualified = development_passed and target_host_qualified and target_runtime_qualified
    state = CapabilityState.TARGET_QUALIFIED if target_qualified else CapabilityState.TESTED if development_passed else CapabilityState.FAILED
    body = {
        "schema": "sentinel-edge-runtime-known-answer-report/1.0",
        "suite_id": item.suite_id,
        "suite_sha256": sha256_bytes(canonical_json_bytes(item.model_dump(mode="json"))),
        "model_graph_sha256": item.model_graph_sha256,
        "runtime_profile_sha256": item.runtime_profile_sha256,
        "session_initialization_repetitions": item.session_initialization_repetitions,
        "session_initialization_ms": initialization_ms,
        "cold_initialization_passed": len(sessions) == item.session_initialization_repetitions,
        "branch_coverage_complete": not missing,
        "case_results": case_results,
        "development_passed": development_passed,
        "target_host_qualified": target_host_qualified,
        "target_runtime_qualified": target_runtime_qualified,
        "target_qualified": target_qualified,
        "service_start_allowed": development_passed,
        "state": state.value,
        "failures": sorted(set(failures)),
    }
    return {**body, "report_digest": sha256_bytes(canonical_json_bytes(body))}
