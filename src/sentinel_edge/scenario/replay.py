"""Explicit reset/accelerated/step-through scenario replay controls."""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field

from sentinel_edge.scenario.engine import DeterministicScenarioEngine, ScenarioResult
from sentinel_edge.security import canonical_json_bytes, sha256_bytes


class ReplayMode(StrEnum):
    RESET = "reset"
    ACCELERATED = "accelerated"
    STEP_THROUGH = "step_through"


class ReplayRun(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: ReplayMode
    result: ScenarioResult
    emission_sha256: str
    step_count: int = Field(ge=0)
    knowledge_snapshots: tuple[dict[str, Any], ...] = ()


class ReplayComparison(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    passed: bool
    modes: tuple[ReplayMode, ...]
    emission_sha256: tuple[str, ...]
    release_orders: tuple[tuple[str, ...], ...]
    mismatch_paths: tuple[str, ...] = ()


def _emission(result: ScenarioResult) -> dict[str, Any]:
    return {"dispatch_order": result.dispatch_order, "final_states": result.final_states, "trace_ids": result.trace_ids, "schedule_digest": result.schedule_digest}


def replay_scenario(
    scenario: dict[str, Any],
    *,
    mode: ReplayMode = ReplayMode.RESET,
    engine_factory: Callable[[], DeterministicScenarioEngine] = DeterministicScenarioEngine,
) -> ReplayRun:
    """Run a scenario under an explicit replay mode.

    The current scenario engine's virtual clock already advances without wall
    sleeps; accelerated mode therefore records that policy explicitly. Step
    through mode exposes one boundary per input observation while retaining the
    same deterministic engine execution.
    """
    if mode not in ReplayMode:
        raise ValueError("unsupported replay mode")
    engine = engine_factory()
    try:
        result = engine.run(scenario)
    finally:
        engine.close()
    return ReplayRun(
        mode=mode,
        result=result,
        emission_sha256=sha256_bytes(canonical_json_bytes(_emission(result))),
        step_count=len(scenario.get("observations", [])) if mode is ReplayMode.STEP_THROUGH else 1,
        knowledge_snapshots=tuple({"observation_id": item.get("observation_id"), "observed_at": item.get("observed_at"),
                                   "known_values": dict(item.get("values", {}))} for item in scenario.get("observations", [])),
    )


def compare_replays(*runs: ReplayRun) -> ReplayComparison:
    if not runs:
        raise ValueError("at least one replay run is required")
    baseline = _emission(runs[0].result)
    mismatches: list[str] = []
    for index, run in enumerate(runs[1:], start=1):
        current = _emission(run.result)
        if current != baseline:
            mismatches.append(f"run[{index}].emission")
    return ReplayComparison(
        passed=not mismatches,
        modes=tuple(run.mode for run in runs),
        emission_sha256=tuple(run.emission_sha256 for run in runs),
        release_orders=tuple(run.result.dispatch_order for run in runs),
        mismatch_paths=tuple(mismatches),
    )
