from __future__ import annotations

from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field


class PairwiseInterferenceReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_: str = Field(default="sentinel-edge-pairwise-interference/1.0", alias="schema")
    hero_workload: str
    co_runner: str
    solo_p99_ms: float = Field(ge=0)
    co_run_p99_ms: float = Field(ge=0)
    p99_inflation_ratio: float = Field(ge=0)
    solo_peak_memory_mb: float = Field(ge=0)
    co_run_peak_memory_mb: float = Field(ge=0)
    memory_delta_mb: float
    solo_sample_count: int = Field(ge=1)
    co_run_sample_count: int = Field(ge=1)
    declared: bool = True


def _p99(values: list[float]) -> float:
    if not values:
        raise ValueError("pairwise comparison requires samples")
    return sorted(values)[max(0, (99 * len(values) + 99) // 100 - 1)]


def measure_pairwise_interference(
    *,
    hero_workload: str,
    co_runner: str,
    solo_latency_ms: Iterable[float],
    co_run_latency_ms: Iterable[float],
    solo_memory_mb: Iterable[float],
    co_run_memory_mb: Iterable[float],
    declared_co_runners: Iterable[str],
) -> PairwiseInterferenceReport:
    if not hero_workload.strip() or not co_runner.strip():
        raise ValueError("workload identities must not be blank")
    if co_runner not in set(declared_co_runners):
        raise ValueError("co-runner must be declared")
    solo_latency = [float(value) for value in solo_latency_ms]
    co_latency = [float(value) for value in co_run_latency_ms]
    solo_memory = [float(value) for value in solo_memory_mb]
    co_memory = [float(value) for value in co_run_memory_mb]
    solo_p99 = _p99(solo_latency)
    co_p99 = _p99(co_latency)
    return PairwiseInterferenceReport(
        hero_workload=hero_workload,
        co_runner=co_runner,
        solo_p99_ms=solo_p99,
        co_run_p99_ms=co_p99,
        p99_inflation_ratio=co_p99 / solo_p99 if solo_p99 else 0.0,
        solo_peak_memory_mb=max(solo_memory),
        co_run_peak_memory_mb=max(co_memory),
        memory_delta_mb=max(co_memory) - max(solo_memory),
        solo_sample_count=len(solo_latency),
        co_run_sample_count=len(co_latency),
    )
