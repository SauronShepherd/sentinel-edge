from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from sentinel_edge.domain.models import HealthState


@dataclass(frozen=True)
class StorageHealthReport:
    state: HealthState
    path: str
    writable: bool
    total_bytes: int
    free_bytes: int
    used_bytes: int
    configured_max_bytes: int
    reserve_bytes: int
    reason_codes: tuple[str, ...]


def inspect_storage(path: str | Path, *, configured_max_bytes: int, reserve_bytes: int, forced_read_only: bool = False) -> StorageHealthReport:
    root = Path(path)
    root.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(root)
    reasons: list[str] = []
    writable = os.access(root, os.W_OK) and not forced_read_only
    if not writable:
        reasons.append("medium_read_only_or_unwritable")
        state = HealthState.FAILED
    elif usage.free < reserve_bytes:
        reasons.append("filesystem_free_space_below_reserve")
        state = HealthState.DEGRADED
    else:
        state = HealthState.HEALTHY
    return StorageHealthReport(
        state=state,
        path=str(root),
        writable=writable,
        total_bytes=usage.total,
        free_bytes=usage.free,
        used_bytes=usage.used,
        configured_max_bytes=configured_max_bytes,
        reserve_bytes=reserve_bytes,
        reason_codes=tuple(reasons) if reasons else ("storage_writable",),
    )
