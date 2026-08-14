"""Deterministic worker-recovery and hardware-watchdog policy."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class RecoveryDecision:
    mechanism: str
    allowed: bool
    quarantined: bool
    attempt: int
    reason_code: str


class WorkerRecoveryPolicy:
    """Bound restarts per profile and keep hardware watchdog distinct."""

    def __init__(self, *, max_restarts: int = 3, window_seconds: int = 300) -> None:
        if max_restarts < 1 or window_seconds < 1:
            raise ValueError("recovery bounds must be positive")
        self.max_restarts = max_restarts
        self.window = timedelta(seconds=window_seconds)
        self._failures: dict[str, list[datetime]] = {}
        self._quarantined: set[str] = set()

    def record_failure(self, profile_id: str, *, at: datetime | None = None) -> RecoveryDecision:
        if not profile_id.strip():
            raise ValueError("profile_id is required")
        now = at or datetime.now(timezone.utc)
        if now.tzinfo is None:
            raise ValueError("failure time must be timezone-aware")
        if profile_id in self._quarantined:
            return RecoveryDecision("process_restart", False, True, self.max_restarts, "crash_loop_quarantined")
        recent = [item for item in self._failures.get(profile_id, []) if now - item <= self.window]
        recent.append(now)
        self._failures[profile_id] = recent
        if len(recent) > self.max_restarts:
            self._quarantined.add(profile_id)
            return RecoveryDecision("process_restart", False, True, len(recent), "crash_loop_quarantined")
        return RecoveryDecision("process_restart", True, False, len(recent), "process_restart_allowed")

    def hardware_watchdog_recovery(self, profile_id: str) -> RecoveryDecision:
        if profile_id in self._quarantined:
            return RecoveryDecision("hardware_watchdog", False, True, len(self._failures.get(profile_id, [])), "crash_loop_quarantined")
        return RecoveryDecision("hardware_watchdog", True, False, len(self._failures.get(profile_id, [])), "hardware_watchdog_recovery_distinct")

    def is_quarantined(self, profile_id: str) -> bool:
        return profile_id in self._quarantined
