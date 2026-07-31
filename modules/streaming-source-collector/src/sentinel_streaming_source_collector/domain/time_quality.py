from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True, slots=True)
class TimeQuality:
    captured_at: datetime
    ingested_at: datetime
    boot_id: str
    clock: str = "synchronized"
    watermark: int = 0

    def __post_init__(self) -> None:
        if self.captured_at.tzinfo is None or self.ingested_at.tzinfo is None: raise ValueError("timezone_required")
        if not self.boot_id.strip(): raise ValueError("boot_id_required")
        if self.clock not in {"synchronized", "degraded", "unknown"}: raise ValueError("invalid_clock_quality")
        if self.watermark < 0: raise ValueError("watermark_must_be_nonnegative")

    @property
    def late(self) -> bool: return self.captured_at > self.ingested_at

    @property
    def age_seconds(self) -> float: return max(0.0, (self.ingested_at - self.captured_at).total_seconds())

    @classmethod
    def now(cls, captured_at: datetime, boot_id: str, watermark: int = 0) -> "TimeQuality":
        return cls(captured_at, datetime.now(timezone.utc), boot_id, watermark=watermark)

