"""Local administrator bootstrap/recovery policy with an audit trail."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class AdminAuditEvent:
    action: str
    actor: str
    physical_presence: bool
    token_digest: str


class LocalAdminBootstrap:
    """One-time local bootstrap; no shared or deterministic default password."""

    def __init__(self) -> None:
        self._token_digest: str | None = None
        self._audit: list[AdminAuditEvent] = []

    @staticmethod
    def _digest(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def bootstrap(self, *, actor: str, physical_presence: bool) -> str:
        if self._token_digest is not None:
            raise RuntimeError("administrator bootstrap already completed")
        if not actor.strip() or not physical_presence:
            raise PermissionError("administrator bootstrap requires local physical presence")
        token = secrets.token_urlsafe(32)
        self._token_digest = self._digest(token)
        self._audit.append(AdminAuditEvent("bootstrap", actor, True, self._token_digest))
        return token

    def recover(self, *, actor: str, physical_presence: bool) -> str:
        if self._token_digest is None:
            raise RuntimeError("administrator bootstrap is required before recovery")
        if not actor.strip() or not physical_presence:
            raise PermissionError("administrator recovery requires local physical presence")
        token = secrets.token_urlsafe(32)
        self._token_digest = self._digest(token)
        self._audit.append(AdminAuditEvent("recovery", actor, True, self._token_digest))
        return token

    def audit(self) -> tuple[AdminAuditEvent, ...]:
        return tuple(self._audit)

