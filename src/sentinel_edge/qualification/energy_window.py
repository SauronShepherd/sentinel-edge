"""Complete-node energy measurement over an explicit scenario window."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompleteNodeEnergyWindow:
    scenario_id: str
    start_monotonic_seconds: float
    end_monotonic_seconds: float
    components_watt_seconds: dict[str, float]
    instrumentation_permitted: bool = True

    def __post_init__(self) -> None:
        if not self.scenario_id.strip() or self.end_monotonic_seconds <= self.start_monotonic_seconds:
            raise ValueError("scenario and positive measurement window are required")
        required = {"camera", "storage", "cooling", "idle"}
        if self.instrumentation_permitted and not required.issubset(self.components_watt_seconds):
            raise ValueError("complete-node components are required when instrumentation permits")
        if any(value < 0 for value in self.components_watt_seconds.values()):
            raise ValueError("energy components cannot be negative")

    @property
    def duration_seconds(self) -> float:
        return self.end_monotonic_seconds - self.start_monotonic_seconds

    @property
    def total_watt_seconds(self) -> float:
        return sum(self.components_watt_seconds.values())
