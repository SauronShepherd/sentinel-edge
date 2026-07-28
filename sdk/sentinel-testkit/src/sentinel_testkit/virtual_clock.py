from datetime import datetime, timezone, timedelta

class VirtualClock:
    def __init__(self, start: datetime | None = None) -> None:
        self.current = start or datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.monotonic = 0.0
        self.events: list[datetime] = []
    def now(self) -> datetime: return self.current
    def monotonic_time(self) -> float: return self.monotonic
    def event_time(self) -> datetime: return self.events[-1] if self.events else self.current
    def advance(self, seconds: float) -> datetime:
        if seconds < 0: raise ValueError("clock cannot move backwards")
        self.current += timedelta(seconds=seconds); self.monotonic += seconds; self.events.append(self.current); return self.current
