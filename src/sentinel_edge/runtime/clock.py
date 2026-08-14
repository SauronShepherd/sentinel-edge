from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Protocol


class Clock(Protocol):
    def now_utc(self) -> datetime: ...
    def monotonic_ns(self) -> int: ...


class SystemClock:
    def now_utc(self) -> datetime:
        return datetime.now(timezone.utc)

    def monotonic_ns(self) -> int:
        return time.monotonic_ns()


class VirtualClock:
    """Deterministic clock for scenarios, recovery tests, and benchmark replay."""

    def __init__(self, now: datetime | None = None, monotonic_ns: int = 0) -> None:
        self._now = now or datetime(2026, 1, 1, tzinfo=timezone.utc)
        self._monotonic_ns = monotonic_ns

    def now_utc(self) -> datetime:
        return self._now

    def monotonic_ns(self) -> int:
        return self._monotonic_ns

    def advance_ms(self, milliseconds: int) -> None:
        if milliseconds < 0:
            raise ValueError("cannot move virtual clock backwards")
        self._now += timedelta(milliseconds=milliseconds)
        self._monotonic_ns += milliseconds * 1_000_000

    def step_utc(self, delta: timedelta) -> None:
        """Model a wall-clock discontinuity without changing monotonic time."""
        self._now += delta
