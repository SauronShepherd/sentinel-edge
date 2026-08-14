from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from sentinel_edge.domain.models import AuthorizationDecision, PrincipalRef, PrincipalRole
from sentinel_edge.security.digests import canonical_json_bytes, sha256_bytes


class AuthenticationError(ValueError):
    pass


class AuthorizationError(PermissionError):
    pass


@dataclass(frozen=True)
class ProducerIdentityDecision:
    allowed: bool
    reason: str


def authorize_producer_identity(principal: PrincipalRef, *, sending_component: str) -> ProducerIdentityDecision:
    """Bind machine principals to the authenticated producer component."""
    component = sending_component.strip()
    if not component:
        return ProducerIdentityDecision(False, "sending_component_required")
    if principal.principal_kind in {"service", "device", "system"} and principal.principal_id != component:
        return ProducerIdentityDecision(False, "producer_identity_mismatch_audited")
    return ProducerIdentityDecision(True, "producer_identity_bound")


@dataclass(frozen=True)
class TokenRecord:
    token_sha256: str
    principal: PrincipalRef
    expires_at: datetime | None = None
    disabled: bool = False


_ROLE_PERMISSIONS: dict[PrincipalRole, frozenset[str]] = {
    PrincipalRole.VIEWER: frozenset({
        "health:read",
        "incidents:read",
        "runtime:read",
        "configuration:read",
        "notifications:read",
        "sources:read",
        "reviews:read",
        "evidence:read",
        "storage:read",
    }),
    PrincipalRole.OPERATOR: frozenset({
        "health:read",
        "incidents:read",
        "runtime:read",
        "configuration:read",
        "notifications:read",
        "sources:read",
        "reviews:read",
        "evidence:read",
        "evidence:write",
        "incidents:command",
        "scenarios:run",
        "incidents:acknowledge",
        "incidents:snooze",
        "notifications:dispatch",
        "reviews:generate",
        "storage:read",
        "spool:reconcile",
    }),
    PrincipalRole.ADMIN: frozenset({"*"}),
}


class AuthManager:
    """Local token authentication with explicit principal, role, and trust epochs.

    Tokens are high-entropy bearer secrets. Only SHA-256 digests are retained. The
    deterministic development tokens are intentionally marked development-only and
    must never be admitted by a field release profile.
    """

    def __init__(self, records: Iterable[tuple[str, PrincipalRef]], *, development_only: bool = False) -> None:
        self.development_only = development_only
        self._records: dict[str, TokenRecord] = {}
        for token, principal in records:
            self.add_token(token, principal)

    @staticmethod
    def _digest_token(token: str) -> str:
        return sha256_bytes(token.encode("utf-8"))

    def add_token(self, token: str, principal: PrincipalRef, *, expires_at: datetime | None = None) -> None:
        if len(token) < 16:
            raise ValueError("bearer token must contain at least 16 characters")
        digest = self._digest_token(token)
        if digest in self._records:
            raise ValueError("duplicate bearer token")
        self._records[digest] = TokenRecord(digest, principal, expires_at)

    def authenticate(self, token: str | None, *, now: datetime | None = None) -> PrincipalRef:
        now = now or datetime.now(timezone.utc)
        if not token:
            raise AuthenticationError("missing bearer token")
        digest = self._digest_token(token)
        record = self._records.get(digest)
        if record is None or not secrets.compare_digest(record.token_sha256, digest):
            raise AuthenticationError("invalid bearer token")
        if record.disabled:
            raise AuthenticationError("bearer token is disabled")
        if record.expires_at is not None and record.expires_at <= now:
            raise AuthenticationError("bearer token is expired")
        return record.principal

    def authorize(self, principal: PrincipalRef, permission: str) -> None:
        if principal.principal_kind in {"service", "device", "system"} and permission == "reviews:generate":
            raise AuthorizationError("non-human principal cannot exercise operator review authority")
        permissions: set[str] = set()
        for role in principal.roles:
            permissions.update(_ROLE_PERMISSIONS[role])
        if "*" not in permissions and permission not in permissions:
            raise AuthorizationError(f"permission denied: {permission}")

    def disable_token(self, token: str) -> PrincipalRef:
        digest = self._digest_token(token)
        record = self._records.get(digest)
        if record is None or not secrets.compare_digest(record.token_sha256, digest):
            raise AuthenticationError("invalid bearer token")
        self._records[digest] = TokenRecord(
            token_sha256=record.token_sha256,
            principal=record.principal,
            expires_at=record.expires_at,
            disabled=True,
        )
        return record.principal

    def disable_principal(self, principal_id: str) -> int:
        changed = 0
        for digest, record in tuple(self._records.items()):
            if record.principal.principal_id == principal_id and not record.disabled:
                self._records[digest] = TokenRecord(
                    token_sha256=record.token_sha256,
                    principal=record.principal,
                    expires_at=record.expires_at,
                    disabled=True,
                )
                changed += 1
        return changed

    @classmethod
    def development(cls) -> "AuthManager":
        return cls(
            [
                (
                    "sentinel-dev-viewer-token",
                    PrincipalRef(principal_id="development-viewer", roles=(PrincipalRole.VIEWER,)),
                ),
                (
                    "sentinel-dev-operator-token",
                    PrincipalRef(principal_id="development-operator", roles=(PrincipalRole.OPERATOR,)),
                ),
                (
                    "sentinel-dev-admin-token",
                    PrincipalRef(principal_id="development-admin", roles=(PrincipalRole.ADMIN,)),
                ),
            ],
            development_only=True,
        )

    @classmethod
    def from_environment(cls) -> "AuthManager":
        token = os.environ.get("SENTINEL_EDGE_ADMIN_TOKEN")
        if not token:
            raise RuntimeError("SENTINEL_EDGE_ADMIN_TOKEN is required outside development mode")
        principal = PrincipalRef(principal_id="local-admin", roles=(PrincipalRole.ADMIN,))
        return cls([(token, principal)], development_only=False)


class CommandAuthorizer:
    CANONICAL_ENCODING_VERSION = "sentinel-cjson-v1"
    """Binds an authorization decision to exact payload, principal, target, and epochs."""

    def __init__(self, secret: bytes, *, policy_version: str = "local-policy-v1", ttl_seconds: int = 30) -> None:
        if len(secret) < 32:
            raise ValueError("authorization secret must contain at least 32 bytes")
        self._secret = secret
        self.policy_version = policy_version
        self.ttl_seconds = ttl_seconds

    @classmethod
    def development(cls) -> "CommandAuthorizer":
        return cls(hashlib.sha256(b"sentinel-edge-development-command-authorizer-v1").digest())

    @staticmethod
    def payload_digest(payload: Any) -> str:
        if hasattr(payload, "model_dump"):
            payload = payload.model_dump(mode="json")
        return sha256_bytes(canonical_json_bytes(payload))

    def _tag_payload(
        self,
        *,
        principal: PrincipalRef,
        operation: str,
        target: str,
        payload_sha256: str,
        accepted_at: datetime,
        expires_at: datetime,
    ) -> bytes:
        return canonical_json_bytes(
            {
                "principal": principal.model_dump(mode="json"),
                "operation": operation,
                "target": target,
                "payload_sha256": payload_sha256,
                "policy_version": self.policy_version,
                "canonical_encoding_version": self.CANONICAL_ENCODING_VERSION,
                "accepted_at": accepted_at.isoformat(),
                "expires_at": expires_at.isoformat(),
            }
        )

    def decide(
        self,
        principal: PrincipalRef,
        *,
        operation: str,
        target: str,
        payload: Any,
        accepted_at: datetime | None = None,
    ) -> AuthorizationDecision:
        accepted_at = accepted_at or datetime.now(timezone.utc)
        expires_at = accepted_at + timedelta(seconds=self.ttl_seconds)
        digest = self.payload_digest(payload)
        tag = hmac.new(
            self._secret,
            self._tag_payload(
                principal=principal,
                operation=operation,
                target=target,
                payload_sha256=digest,
                accepted_at=accepted_at,
                expires_at=expires_at,
            ),
            hashlib.sha256,
        ).hexdigest()
        return AuthorizationDecision(
            principal=principal,
            operation=operation,
            target=target,
            payload_sha256=digest,
            policy_version=self.policy_version,
            canonical_encoding_version=self.CANONICAL_ENCODING_VERSION,
            accepted_at=accepted_at,
            expires_at=expires_at,
            authorization_tag=tag,
        )

    def verify(
        self,
        decision: AuthorizationDecision,
        *,
        payload: Any,
        operation: str,
        target: str,
        current_principal: PrincipalRef | None = None,
        now: datetime | None = None,
    ) -> None:
        now = now or datetime.now(timezone.utc)
        if decision.expires_at <= now:
            raise AuthorizationError("authorization decision expired")
        if decision.canonical_encoding_version != self.CANONICAL_ENCODING_VERSION:
            raise AuthorizationError("authorization canonical encoding version mismatch")
        if decision.operation != operation or decision.target != target:
            raise AuthorizationError("authorization operation or target mismatch")
        digest = self.payload_digest(payload)
        if not secrets.compare_digest(digest, decision.payload_sha256):
            raise AuthorizationError("authorization payload mismatch")
        if current_principal is not None and decision.principal != current_principal:
            raise AuthorizationError("authorization principal or trust epoch changed")
        expected = hmac.new(
            self._secret,
            self._tag_payload(
                principal=decision.principal,
                operation=decision.operation,
                target=decision.target,
                payload_sha256=decision.payload_sha256,
                accepted_at=decision.accepted_at,
                expires_at=decision.expires_at,
            ),
            hashlib.sha256,
        ).hexdigest()
        if not secrets.compare_digest(expected, decision.authorization_tag):
            raise AuthorizationError("authorization tag invalid")

    @staticmethod
    def scoped_idempotency_key(
        principal: PrincipalRef,
        *,
        operation: str,
        target: str,
        client_key: str,
    ) -> str:
        return sha256_bytes(
            canonical_json_bytes(
                {
                    "principal_id": principal.principal_id,
                    "session_epoch": principal.session_epoch,
                    "device_trust_epoch": principal.device_trust_epoch,
                    "canonical_encoding_version": CommandAuthorizer.CANONICAL_ENCODING_VERSION,
                    "operation": operation,
                    "target": target,
                    "client_key": client_key,
                }
            )
        )


def generate_bearer_token() -> str:
    """Return a URL-safe bearer secret with 256 bits of CSPRNG entropy."""
    return secrets.token_urlsafe(32)
