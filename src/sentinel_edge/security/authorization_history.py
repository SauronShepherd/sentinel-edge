"""Bounded same-boot point-in-time authorization and outcome history."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class AuthorizationOutcome:
    command_id: str
    principal: str
    operation: str
    target: str
    boot_id: str
    issued_at: datetime
    expires_at: datetime
    original_allowed: bool
    commit_allowed: bool | None = None
    reason: str = ""

    def commit(self, *, now: datetime, boot_id: str, allowed: bool, reason: str) -> "AuthorizationOutcome":
        if boot_id != self.boot_id or now.tzinfo is None or now > self.expires_at:
            return AuthorizationOutcome(**{**self.__dict__, "commit_allowed": False, "reason": "same_boot_or_expired"})
        return AuthorizationOutcome(**{**self.__dict__, "commit_allowed": allowed, "reason": reason})


def issue_authorization(command_id: str, principal: str, operation: str, target: str, *, boot_id: str, now: datetime, ttl: timedelta = timedelta(seconds=30), allowed: bool = True) -> AuthorizationOutcome:
    if not all(value.strip() for value in (command_id, principal, operation, target, boot_id)) or now.tzinfo is None or ttl <= timedelta(0):
        raise ValueError("bounded authorization fields are invalid")
    return AuthorizationOutcome(command_id, principal, operation, target, boot_id, now, now + ttl, allowed, None, "issued")
