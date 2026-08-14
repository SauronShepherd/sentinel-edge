"""Immutable records for mutable platform/provider observations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("observation times must be timezone-aware")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class FrozenArtifactRef:
    artifact_id: str
    sha256: str

    def __post_init__(self) -> None:
        if not self.artifact_id.strip() or len(self.sha256) != 64:
            raise ValueError("frozen artifact references require an id and sha256")


@dataclass(frozen=True)
class PlatformObservation:
    observation_id: str
    provider: str
    state: dict[str, Any]
    effective_from: datetime
    effective_until: datetime | None = None
    source_artifacts: tuple[FrozenArtifactRef, ...] = ()

    def __post_init__(self) -> None:
        if not self.observation_id.strip() or not self.provider.strip():
            raise ValueError("observation identity is required")
        start = _utc(self.effective_from)
        end = _utc(self.effective_until) if self.effective_until else None
        if end is not None and end <= start:
            raise ValueError("effective_until must be after effective_from")
        if not isinstance(self.state, dict) or not self.state:
            raise ValueError("mutable observation state must be a non-empty mapping")

    def applies_at(self, instant: datetime) -> bool:
        point = _utc(instant)
        start = _utc(self.effective_from)
        end = _utc(self.effective_until) if self.effective_until else None
        return start <= point and (end is None or point < end)


def observation_at(observations: tuple[PlatformObservation, ...] | list[PlatformObservation], instant: datetime) -> PlatformObservation | None:
    """Resolve the observation valid at an instant without consulting current mutable state."""
    matches = [item for item in observations if item.applies_at(instant)]
    if len(matches) > 1:
        raise ValueError("overlapping platform observation intervals")
    return matches[0] if matches else None
