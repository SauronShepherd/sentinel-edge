"""Deterministic I/O pressure shedding that protects critical truth."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IoSheddingDecision:
    pressure_active: bool
    critical_truth_preserved: bool
    shed: tuple[str, ...]
    degraded: bool


def decide_io_shedding(*, pressure_active: bool) -> IoSheddingDecision:
    if not pressure_active:
        return IoSheddingDecision(False, True, (), False)
    return IoSheddingDecision(True, True, ("previews", "optional_transcoding", "telemetry", "research_exports", "backup", "garbage_collection"), True)
