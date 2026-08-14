from datetime import datetime, timezone

import pytest

from sentinel_edge.evidence.state_events import EvidenceStateEvent, EvidenceStateEventKind, append_state_event, current_binding


def _event(event_id: str, kind: EvidenceStateEventKind, second: int, digest: str | None) -> EvidenceStateEvent:
    return EvidenceStateEvent(event_id, "e1", kind, datetime(2026, 1, 1, 0, 0, second, tzinfo=timezone.utc), "p1", "a" * 64, "p2" if digest else None, digest, "test")


def test_state_changes_are_append_only_and_historical_fields_survive() -> None:
    first = _event("1", EvidenceStateEventKind.EXTERNAL_LOSS, 1, None)
    second = _event("2", EvidenceStateEventKind.RESTORE, 2, "b" * 64)
    history = append_state_event(append_state_event((), first), second)
    assert history[0].kind is EvidenceStateEventKind.EXTERNAL_LOSS
    assert history[0].prior_content_sha256 == "a" * 64
    assert current_binding(history) == ("p2", "b" * 64)


def test_duplicate_or_backwards_events_fail_closed() -> None:
    first = _event("1", EvidenceStateEventKind.REDACTION, 2, None)
    with pytest.raises(ValueError):
        append_state_event((first,), _event("1", EvidenceStateEventKind.RESTORE, 3, "b" * 64))
    with pytest.raises(ValueError):
        append_state_event((first,), _event("2", EvidenceStateEventKind.RESTORE, 1, "b" * 64))
