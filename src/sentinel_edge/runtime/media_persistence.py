"""Explicit incident truth when rich-media persistence is unavailable."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MediaPersistenceOutcome:
    incident_transition_recorded: bool
    media_persisted: bool
    media_reference: str | None
    state: str

    def __post_init__(self) -> None:
        if not self.incident_transition_recorded:
            raise ValueError("incident transition cannot be silently dropped")
        if self.media_persisted and not self.media_reference:
            raise ValueError("persisted media requires a reference")
        if not self.media_persisted and self.state not in {"degraded", "evidence-unavailable"}:
            raise ValueError("media persistence failure requires explicit degraded state")

    def complete_bundle(self) -> bool:
        return self.media_persisted and self.media_reference is not None
