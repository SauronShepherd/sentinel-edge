from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum


class MaintenanceAction(StrEnum):
    WAL_CHECKPOINT = "wal_checkpoint"
    BACKUP = "backup"
    COMPACTION = "compaction"
    ARTIFACT_GC = "artifact_gc"


class MaintenanceDisposition(StrEnum):
    RUN = "run"
    DEFERRED = "deferred"
    FORCED = "forced"


@dataclass(frozen=True)
class MaintenanceDecision:
    action: MaintenanceAction
    disposition: MaintenanceDisposition
    decided_at: datetime
    tier_a_protected_window: bool
    storage_pressure: bool
    safety_required: bool
    reason_codes: tuple[str, ...]
    expected_service_consequence: str


class MaintenanceCoordinator:
    """Keeps persistence maintenance outside Tier-A windows unless safety/storage pressure wins."""

    def __init__(self) -> None:
        self._history: list[MaintenanceDecision] = []

    def decide(
        self,
        action: MaintenanceAction,
        *,
        tier_a_protected_window: bool,
        storage_pressure: bool = False,
        safety_required: bool = False,
        now: datetime | None = None,
    ) -> MaintenanceDecision:
        now = now or datetime.now(timezone.utc)
        if tier_a_protected_window and not storage_pressure and not safety_required:
            disposition = MaintenanceDisposition.DEFERRED
            reasons = ("tier_a_protected_window", "maintenance_deferred")
            consequence = "none_expected"
        elif tier_a_protected_window:
            disposition = MaintenanceDisposition.FORCED
            reasons = tuple(sorted({
                "tier_a_protected_window",
                "storage_pressure" if storage_pressure else "safety_required",
                "maintenance_forced",
            }))
            consequence = "tier_a_latency_may_increase_and_must_be_measured"
        else:
            disposition = MaintenanceDisposition.RUN
            reasons = ("outside_tier_a_window",)
            consequence = "background_io_only"
        decision = MaintenanceDecision(
            action=action,
            disposition=disposition,
            decided_at=now,
            tier_a_protected_window=tier_a_protected_window,
            storage_pressure=storage_pressure,
            safety_required=safety_required,
            reason_codes=reasons,
            expected_service_consequence=consequence,
        )
        self._history.append(decision)
        return decision

    def history(self) -> tuple[MaintenanceDecision, ...]:
        return tuple(self._history)
