from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sentinel_edge.projections.cursor_policy import validate_cursor


def test_cursor_is_opaque_and_expires() -> None:
    cursor = f"{uuid4()}:4:2:{'a' * 64}"
    issued = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert validate_cursor(cursor, issued_at=issued, now=issued + timedelta(minutes=1))
    assert not validate_cursor(cursor, issued_at=issued, now=issued + timedelta(minutes=16))
    assert not validate_cursor(cursor.replace('a' * 64, 'principal-secret'), issued_at=issued, now=issued)
