from dataclasses import dataclass
from datetime import datetime
from typing import Mapping

_UNITS = frozenset({"celsius", "percent", "m/s", "mm", "lux", "degrees", "g", "count"})
_QUALITY = frozenset({"good", "uncertain", "bad", "missing"})

@dataclass(frozen=True, slots=True)
class Observation:
    source_id: str
    metric: str
    value: float | int | None
    unit: str
    captured_at: datetime
    quality: str = "good"
    metadata: Mapping[str, str] = ()

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.metric.strip(): raise ValueError("identity_required")
        if self.captured_at.tzinfo is None: raise ValueError("captured_at_must_be_timezone_aware")
        if self.unit not in _UNITS: raise ValueError("unsupported_unit")
        if self.quality not in _QUALITY: raise ValueError("invalid_quality")
        if self.quality == "missing" and self.value is not None: raise ValueError("missing_value_must_be_null")
        if self.quality != "missing" and self.value is None: raise ValueError("value_required")

