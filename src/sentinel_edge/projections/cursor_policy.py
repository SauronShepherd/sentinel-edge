"""Bounded cursor lifetime and privacy-safe validation."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID


def validate_cursor(value: str, *, issued_at: datetime, now: datetime | None = None, max_age: timedelta = timedelta(minutes=15), max_buffer: int = 32) -> bool:
    if max_age <= timedelta(0) or max_buffer < 1 or issued_at.tzinfo is None:
        raise ValueError("invalid cursor policy")
    parts = value.split(":")
    if len(parts) != 4:
        return False
    try:
        UUID(parts[0]); int(parts[1]); int(parts[2])
    except (ValueError, TypeError):
        return False
    scope = parts[3]
    if len(scope) != 64 or any(char not in "0123456789abcdef" for char in scope.lower()):
        return False
    current = now or datetime.now(timezone.utc)
    if current.astimezone(timezone.utc) - issued_at.astimezone(timezone.utc) > max_age:
        return False
    return True
