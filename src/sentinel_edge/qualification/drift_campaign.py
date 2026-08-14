"""Deterministic drift campaign scenarios and safe actions."""
from __future__ import annotations

from dataclasses import dataclass


SCENARIOS = ("brightness_scene", "sensor_bias_noise", "missingness", "source_version", "prevalence_shift")


@dataclass(frozen=True)
class DriftScenarioResult:
    scenario: str
    classification: str
    limitation: str
    safe_action: str
    synthetic_only: bool = True


def evaluate_drift_scenario(scenario: str) -> DriftScenarioResult:
    if scenario not in SCENARIOS:
        raise ValueError("unknown drift scenario")
    return DriftScenarioResult(scenario, "synthetic_shift_observed", "does_not_prove_real_world_concept_drift", "review_and_abstain")
