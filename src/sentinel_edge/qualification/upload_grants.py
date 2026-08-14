"""Deterministic direct-upload grant lifecycle controls."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(frozen=True)
class UploadGrant:
    grant_id: UUID
    principal_id: str
    boot_id: str
    scope: str
    expires_at: datetime
    max_bytes: int
    consumed: bool = False

    def __post_init__(self) -> None:
        if not self.principal_id.strip() or not self.boot_id.strip() or not self.scope.strip():
            raise ValueError("upload grant identity and scope are required")
        if self.expires_at.tzinfo is None:
            raise ValueError("upload grant expiry must be timezone-aware")
        if self.max_bytes <= 0:
            raise ValueError("upload grant max_bytes must be positive")


@dataclass(frozen=True)
class UploadGrantDecision:
    accepted: bool
    code: str
    grant: UploadGrant


class UploadGrantAuthority:
    def __init__(self, *, boot_id: str) -> None:
        if not boot_id.strip():
            raise ValueError("boot_id is required")
        self.boot_id = boot_id
        self._grants: dict[UUID, UploadGrant] = {}

    def issue(self, *, principal_id: str, scope: str, expires_at: datetime, max_bytes: int) -> UploadGrant:
        grant = UploadGrant(uuid4(), principal_id, self.boot_id, scope, expires_at, max_bytes)
        self._grants[grant.grant_id] = grant
        return grant

    def consume(self, grant_id: UUID, *, principal_id: str, scope: str, now: datetime | None = None) -> UploadGrantDecision:
        now = now or datetime.now(timezone.utc)
        grant = self._grants.get(grant_id)
        if grant is None:
            return UploadGrantDecision(False, "unknown_grant", UploadGrant(grant_id, principal_id or "unknown", self.boot_id, scope or "unknown", now, 1))
        if grant.consumed:
            return UploadGrantDecision(False, "grant_already_consumed", grant)
        if grant.boot_id != self.boot_id:
            return UploadGrantDecision(False, "grant_boot_mismatch", grant)
        if grant.principal_id != principal_id:
            return UploadGrantDecision(False, "grant_principal_mismatch", grant)
        if grant.scope != scope:
            return UploadGrantDecision(False, "grant_scope_mismatch", grant)
        if now >= grant.expires_at:
            return UploadGrantDecision(False, "grant_expired", grant)
        consumed = UploadGrant(**{**grant.__dict__, "consumed": True})
        self._grants[grant_id] = consumed
        return UploadGrantDecision(True, "accepted", consumed)
