"""Reserved capacity policy for critical incident truth and disposition records."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CriticalIoReserve:
    reserve_bytes: int
    append_bytes_limit: int
    fsync_tail_seconds_limit: float

    def __post_init__(self) -> None:
        if self.reserve_bytes <= 0 or self.append_bytes_limit <= 0 or self.fsync_tail_seconds_limit <= 0:
            raise ValueError("critical reserve and append/fsync limits must be positive")

    def optional_write_allowed(self, *, free_bytes: int, write_bytes: int) -> bool:
        return free_bytes - write_bytes >= self.reserve_bytes

    def critical_write_allowed(self, *, write_bytes: int) -> bool:
        return 0 <= write_bytes <= self.append_bytes_limit
