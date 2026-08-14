from datetime import datetime, timedelta, timezone

from sentinel_edge.security.authorization_history import issue_authorization


def test_authorization_preserves_original_and_commit_outcomes() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    record = issue_authorization("c1", "p1", "low-impact", "target", boot_id="b1", now=now)
    committed = record.commit(now=now + timedelta(seconds=1), boot_id="b1", allowed=False, reason="role_changed")
    assert committed.original_allowed is True
    assert committed.commit_allowed is False
    assert committed.reason == "role_changed"


def test_expired_or_wrong_boot_cannot_extend_authority() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    record = issue_authorization("c1", "p1", "low-impact", "target", boot_id="b1", now=now, ttl=timedelta(seconds=1))
    assert record.commit(now=now + timedelta(seconds=2), boot_id="b1", allowed=True, reason="ok").commit_allowed is False
    assert record.commit(now=now, boot_id="b2", allowed=True, reason="ok").commit_allowed is False
