"""Append-only evidence state events that preserve historical provenance."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum


class EvidenceStateEventKind(StrEnum):
    REDACTION = "redaction"
    ERASURE = "erasure"
    EXTERNAL_LOSS = "external_loss"
    RESTORE = "restore"
    REBINDING = "rebinding"


@dataclass(frozen=True)
class EvidenceStateEvent:
    event_id: str
    evidence_id: str
    kind: EvidenceStateEventKind
    occurred_at: datetime
    prior_digest_profile: str | None
    prior_content_sha256: str | None
    resulting_digest_profile: str | None
    resulting_content_sha256: str | None
    source: str

    def __post_init__(self) -> None:
        if not self.event_id.strip() or not self.evidence_id.strip() or not self.source.strip():
            raise ValueError("state event identity and source are required")
        if self.occurred_at.tzinfo is None:
            raise ValueError("state event time must be timezone-aware")


def append_state_event(history: tuple[EvidenceStateEvent, ...], event: EvidenceStateEvent) -> tuple[EvidenceStateEvent, ...]:
    if history and event.occurred_at < history[-1].occurred_at:
        raise ValueError("append-only evidence history cannot move backwards")
    if any(item.event_id == event.event_id for item in history):
        raise ValueError("duplicate evidence state event")
    return (*history, event)


def current_binding(history: tuple[EvidenceStateEvent, ...]) -> tuple[str | None, str | None]:
    """Return the latest binding without rewriting prior event fields."""
    if not history:
        return None, None
    latest = history[-1]
    return latest.resulting_digest_profile, latest.resulting_content_sha256
