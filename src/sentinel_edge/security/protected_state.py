from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sentinel_edge.domain.models import PrincipalRef
from sentinel_edge.security.digests import canonical_json_bytes, sha256_bytes


class GrantState(StrEnum):
    ACTIVE = "active"
    RETIRED = "retired"
    REVOKED_POLICY = "revoked_policy"
    SUSPECTED_COMPROMISE = "suspected_compromise"
    COMPROMISED = "compromised"
    EXPIRED = "expired"


class GrantLifecycleAction(StrEnum):
    ACTIVATE = "activate"
    LOGOUT = "logout"
    DEVICE_REVOCATION = "device_revocation"
    RETENTION_EXPIRY = "retention_expiry"
    PLANNED_RETIREMENT = "planned_retirement"
    POLICY_REVOCATION = "policy_revocation"
    SUSPECT_COMPROMISE = "suspect_compromise"
    CONFIRM_COMPROMISE = "confirm_compromise"


_ACTION_STATE = {
    GrantLifecycleAction.ACTIVATE: GrantState.ACTIVE,
    GrantLifecycleAction.LOGOUT: GrantState.REVOKED_POLICY,
    GrantLifecycleAction.DEVICE_REVOCATION: GrantState.REVOKED_POLICY,
    GrantLifecycleAction.RETENTION_EXPIRY: GrantState.EXPIRED,
    GrantLifecycleAction.PLANNED_RETIREMENT: GrantState.RETIRED,
    GrantLifecycleAction.POLICY_REVOCATION: GrantState.REVOKED_POLICY,
    GrantLifecycleAction.SUSPECT_COMPROMISE: GrantState.SUSPECTED_COMPROMISE,
    GrantLifecycleAction.CONFIRM_COMPROMISE: GrantState.COMPROMISED,
}


class LocalAccessGrant(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    grant_id: UUID
    principal_id: str
    session_epoch: int = Field(ge=0)
    device_trust_epoch: int = Field(ge=0)
    scope: tuple[str, ...]
    issued_at: datetime
    expires_at: datetime
    state: GrantState = GrantState.ACTIVE

    @field_validator("principal_id")
    @classmethod
    def principal_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("grant principal_id must not be blank")
        return value

    @model_validator(mode="after")
    def validate_grant(self) -> "LocalAccessGrant":
        if self.expires_at <= self.issued_at:
            raise ValueError("grant expiry must follow issue time")
        if not self.scope:
            raise ValueError("grant requires at least one scope")
        return self


class ProtectedStatePurgeReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    receipt_id: UUID
    grant_id: UUID
    action: GrantLifecycleAction
    resulting_state: GrantState
    principal_id: str
    purged_cache_entries: int = Field(ge=0)
    purged_queued_authority: int = Field(ge=0)
    purged_payload_sha256: tuple[str, ...]
    actor: str
    reason: str
    created_at: datetime
    receipt_sha256: str


class ProtectedLocalStateStore:
    """Protected local cache and queued-authority store with durable revocation.

    Cache/queue payloads are encrypted-at-rest out of scope for this development
    implementation; this service proves scope, expiry, purge, and historical grant
    identity. It therefore remains non-release-eligible until an approved storage
    encryption profile is bound.
    """

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=FULL")
        self._connection.execute("PRAGMA busy_timeout=5000")
        self._connection.row_factory = sqlite3.Row
        self._lock = RLock()
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS local_access_grants (
                grant_id TEXT PRIMARY KEY,
                principal_id TEXT NOT NULL,
                session_epoch INTEGER NOT NULL,
                device_trust_epoch INTEGER NOT NULL,
                state TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS grant_lifecycle_events (
                event_id TEXT PRIMARY KEY,
                grant_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resulting_state TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS protected_cache_entries (
                cache_id TEXT PRIMARY KEY,
                grant_id TEXT NOT NULL,
                key_sha256 TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                payload BLOB NOT NULL,
                retention_expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(grant_id,key_sha256)
            );
            CREATE TABLE IF NOT EXISTS queued_authority (
                queue_id TEXT PRIMARY KEY,
                grant_id TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS protected_state_purge_receipts (
                receipt_id TEXT PRIMARY KEY,
                grant_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            """
        )

    def create_grant(
        self,
        principal: PrincipalRef,
        *,
        scope: tuple[str, ...],
        expires_at: datetime,
        issued_at: datetime | None = None,
    ) -> LocalAccessGrant:
        issued_at = issued_at or datetime.now(timezone.utc)
        seed = {
            "principal_id": principal.principal_id,
            "session_epoch": principal.session_epoch,
            "device_trust_epoch": principal.device_trust_epoch,
            "scope": sorted(scope),
            "issued_at": issued_at.isoformat(),
            "expires_at": expires_at.isoformat(),
        }
        grant_id = uuid5(NAMESPACE_URL, f"sentinel-local-grant:{sha256_bytes(canonical_json_bytes(seed))}")
        grant = LocalAccessGrant(
            grant_id=grant_id,
            principal_id=principal.principal_id,
            session_epoch=principal.session_epoch,
            device_trust_epoch=principal.device_trust_epoch,
            scope=tuple(sorted(set(scope))),
            issued_at=issued_at,
            expires_at=expires_at,
        )
        with self._lock, self._connection:
            row = self._connection.execute(
                "SELECT payload_json FROM local_access_grants WHERE grant_id=?", (str(grant_id),)
            ).fetchone()
            if row is not None:
                return LocalAccessGrant.model_validate(json.loads(row[0]))
            self._connection.execute(
                "INSERT INTO local_access_grants(grant_id,principal_id,session_epoch,device_trust_epoch,state,expires_at,payload_json) VALUES (?,?,?,?,?,?,?)",
                (
                    str(grant_id), grant.principal_id, grant.session_epoch, grant.device_trust_epoch,
                    grant.state.value, grant.expires_at.isoformat(), grant.model_dump_json(),
                ),
            )
            self._record_event(grant, GrantLifecycleAction.ACTIVATE, actor=principal.principal_id, reason="grant_issued", at=issued_at)
        return grant

    def _load(self, grant_id: UUID | str) -> LocalAccessGrant:
        row = self._connection.execute(
            "SELECT payload_json,state FROM local_access_grants WHERE grant_id=?", (str(grant_id),)
        ).fetchone()
        if row is None:
            raise KeyError(str(grant_id))
        return LocalAccessGrant.model_validate(json.loads(row[0])).model_copy(update={"state": GrantState(row[1])})

    def _record_event(
        self, grant: LocalAccessGrant, action: GrantLifecycleAction, *, actor: str, reason: str, at: datetime
    ) -> None:
        payload = {
            "grant_id": str(grant.grant_id),
            "principal_id": grant.principal_id,
            "action": action.value,
            "resulting_state": _ACTION_STATE[action].value,
            "actor": actor,
            "reason": reason,
            "created_at": at.isoformat(),
        }
        event_id = uuid5(NAMESPACE_URL, f"sentinel-grant-event:{sha256_bytes(canonical_json_bytes(payload))}")
        self._connection.execute(
            "INSERT OR IGNORE INTO grant_lifecycle_events(event_id,grant_id,action,resulting_state,created_at,payload_json) VALUES (?,?,?,?,?,?)",
            (str(event_id), str(grant.grant_id), action.value, _ACTION_STATE[action].value, at.isoformat(), json.dumps(payload, sort_keys=True)),
        )

    def _require_active(self, grant_id: UUID | str, *, scope: str | None = None, now: datetime | None = None) -> LocalAccessGrant:
        now = now or datetime.now(timezone.utc)
        grant = self._load(grant_id)
        if grant.state is not GrantState.ACTIVE:
            raise PermissionError("local access grant is not active")
        if grant.expires_at <= now:
            self.revoke(grant.grant_id, action=GrantLifecycleAction.RETENTION_EXPIRY, actor="system", reason="grant_expired", now=now)
            raise PermissionError("local access grant expired")
        if scope is not None and scope not in grant.scope:
            raise PermissionError("local access grant scope mismatch")
        return grant

    def put_cache(
        self,
        grant_id: UUID,
        *,
        key: str,
        payload: bytes,
        retention_expires_at: datetime,
        scope: str = "protected_cache",
        now: datetime | None = None,
    ) -> str:
        now = now or datetime.now(timezone.utc)
        self._require_active(grant_id, scope=scope, now=now)
        if retention_expires_at <= now:
            raise ValueError("cache retention expiry must be in the future")
        key_sha = sha256_bytes(key.encode("utf-8"))
        payload_sha = sha256_bytes(payload)
        cache_id = str(uuid5(NAMESPACE_URL, f"sentinel-protected-cache:{grant_id}:{key_sha}"))
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT INTO protected_cache_entries(cache_id,grant_id,key_sha256,payload_sha256,payload,retention_expires_at,created_at) VALUES (?,?,?,?,?,?,?) ON CONFLICT(grant_id,key_sha256) DO UPDATE SET payload_sha256=excluded.payload_sha256,payload=excluded.payload,retention_expires_at=excluded.retention_expires_at,created_at=excluded.created_at",
                (cache_id, str(grant_id), key_sha, payload_sha, payload, retention_expires_at.isoformat(), now.isoformat()),
            )
        return cache_id

    def read_cache(self, grant_id: UUID, *, key: str, now: datetime | None = None) -> bytes:
        now = now or datetime.now(timezone.utc)
        self._require_active(grant_id, scope="protected_cache", now=now)
        key_sha = sha256_bytes(key.encode("utf-8"))
        row = self._connection.execute(
            "SELECT payload,retention_expires_at FROM protected_cache_entries WHERE grant_id=? AND key_sha256=?",
            (str(grant_id), key_sha),
        ).fetchone()
        if row is None:
            raise KeyError(key)
        if datetime.fromisoformat(row[1]) <= now:
            with self._connection:
                self._connection.execute(
                    "DELETE FROM protected_cache_entries WHERE grant_id=? AND key_sha256=?", (str(grant_id), key_sha)
                )
            raise KeyError(key)
        return bytes(row[0])

    def queue_authority(
        self, grant_id: UUID, *, payload: dict[str, Any], now: datetime | None = None
    ) -> UUID:
        now = now or datetime.now(timezone.utc)
        self._require_active(grant_id, scope="queued_authority", now=now)
        payload_sha = sha256_bytes(canonical_json_bytes(payload))
        queue_id = uuid5(NAMESPACE_URL, f"sentinel-protected-queue:{grant_id}:{payload_sha}")
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT OR IGNORE INTO queued_authority(queue_id,grant_id,payload_sha256,payload_json,created_at) VALUES (?,?,?,?,?)",
                (str(queue_id), str(grant_id), payload_sha, json.dumps(payload, sort_keys=True), now.isoformat()),
            )
        return queue_id

    def revoke(
        self,
        grant_id: UUID | str,
        *,
        action: GrantLifecycleAction,
        actor: str,
        reason: str,
        now: datetime | None = None,
    ) -> ProtectedStatePurgeReceipt:
        if action is GrantLifecycleAction.ACTIVATE:
            raise ValueError("activate is not a revocation action")
        if not actor.strip() or not reason.strip():
            raise ValueError("revocation actor and reason are required")
        now = now or datetime.now(timezone.utc)
        with self._lock, self._connection:
            grant = self._load(grant_id)
            cache_rows = self._connection.execute(
                "SELECT payload_sha256 FROM protected_cache_entries WHERE grant_id=? ORDER BY cache_id", (str(grant.grant_id),)
            ).fetchall()
            queue_rows = self._connection.execute(
                "SELECT payload_sha256 FROM queued_authority WHERE grant_id=? ORDER BY queue_id", (str(grant.grant_id),)
            ).fetchall()
            payload_digests = tuple(sorted({str(row[0]) for row in (*cache_rows, *queue_rows)}))
            self._connection.execute("DELETE FROM protected_cache_entries WHERE grant_id=?", (str(grant.grant_id),))
            self._connection.execute("DELETE FROM queued_authority WHERE grant_id=?", (str(grant.grant_id),))
            resulting_state = _ACTION_STATE[action]
            self._connection.execute(
                "UPDATE local_access_grants SET state=? WHERE grant_id=?", (resulting_state.value, str(grant.grant_id))
            )
            self._record_event(grant, action, actor=actor, reason=reason, at=now)
            base = {
                "grant_id": str(grant.grant_id),
                "action": action.value,
                "resulting_state": resulting_state.value,
                "principal_id": grant.principal_id,
                "purged_cache_entries": len(cache_rows),
                "purged_queued_authority": len(queue_rows),
                "purged_payload_sha256": payload_digests,
                "actor": actor,
                "reason": reason,
                "created_at": now.isoformat(),
            }
            receipt_sha = sha256_bytes(canonical_json_bytes(base))
            receipt = ProtectedStatePurgeReceipt(
                receipt_id=uuid5(NAMESPACE_URL, f"sentinel-protected-purge:{receipt_sha}"),
                grant_id=grant.grant_id,
                action=action,
                resulting_state=resulting_state,
                principal_id=grant.principal_id,
                purged_cache_entries=len(cache_rows),
                purged_queued_authority=len(queue_rows),
                purged_payload_sha256=payload_digests,
                actor=actor,
                reason=reason,
                created_at=now,
                receipt_sha256=receipt_sha,
            )
            self._connection.execute(
                "INSERT OR IGNORE INTO protected_state_purge_receipts(receipt_id,grant_id,created_at,payload_json) VALUES (?,?,?,?)",
                (str(receipt.receipt_id), str(grant.grant_id), now.isoformat(), receipt.model_dump_json()),
            )
            return receipt

    def purge_principal(
        self,
        principal: PrincipalRef,
        *,
        action: GrantLifecycleAction,
        actor: str,
        reason: str,
        now: datetime | None = None,
    ) -> tuple[ProtectedStatePurgeReceipt, ...]:
        rows = self._connection.execute(
            "SELECT grant_id FROM local_access_grants WHERE principal_id=? AND session_epoch=? AND device_trust_epoch=? AND state=?",
            (principal.principal_id, principal.session_epoch, principal.device_trust_epoch, GrantState.ACTIVE.value),
        ).fetchall()
        return tuple(
            self.revoke(row[0], action=action, actor=actor, reason=reason, now=now) for row in rows
        )

    def purge_principal_id(
        self,
        principal_id: str,
        *,
        action: GrantLifecycleAction,
        actor: str,
        reason: str,
        now: datetime | None = None,
    ) -> tuple[ProtectedStatePurgeReceipt, ...]:
        rows = self._connection.execute(
            "SELECT grant_id FROM local_access_grants WHERE principal_id=? AND state=? ORDER BY grant_id",
            (principal_id, GrantState.ACTIVE.value),
        ).fetchall()
        return tuple(
            self.revoke(row[0], action=action, actor=actor, reason=reason, now=now) for row in rows
        )

    def purge_expired(self, *, now: datetime | None = None) -> tuple[ProtectedStatePurgeReceipt, ...]:
        now = now or datetime.now(timezone.utc)
        rows = self._connection.execute(
            "SELECT grant_id FROM local_access_grants WHERE state=? AND expires_at<=? ORDER BY grant_id",
            (GrantState.ACTIVE.value, now.isoformat()),
        ).fetchall()
        return tuple(
            self.revoke(row[0], action=GrantLifecycleAction.RETENTION_EXPIRY, actor="system-retention", reason="retention_expired", now=now)
            for row in rows
        )

    def grants(self) -> tuple[LocalAccessGrant, ...]:
        rows = self._connection.execute(
            "SELECT payload_json,state FROM local_access_grants ORDER BY principal_id,expires_at,grant_id"
        ).fetchall()
        return tuple(
            LocalAccessGrant.model_validate(json.loads(row[0])).model_copy(update={"state": GrantState(row[1])})
            for row in rows
        )

    def receipts(self) -> tuple[ProtectedStatePurgeReceipt, ...]:
        rows = self._connection.execute(
            "SELECT payload_json FROM protected_state_purge_receipts ORDER BY created_at,receipt_id"
        ).fetchall()
        return tuple(ProtectedStatePurgeReceipt.model_validate(json.loads(row[0])) for row in rows)

    def metrics(self) -> dict[str, int | bool | str]:
        cache_count = int(self._connection.execute("SELECT COUNT(*) FROM protected_cache_entries").fetchone()[0])
        queue_count = int(self._connection.execute("SELECT COUNT(*) FROM queued_authority").fetchone()[0])
        active_grants = int(self._connection.execute(
            "SELECT COUNT(*) FROM local_access_grants WHERE state=?", (GrantState.ACTIVE.value,)
        ).fetchone()[0])
        return {
            "active_grants": active_grants,
            "protected_cache_entries": cache_count,
            "queued_authority_items": queue_count,
            "values_encrypted_at_rest": False,
            "release_eligible": False,
            "limitation": "development_scope_without_approved_storage_encryption_profile",
        }

    def close(self) -> None:
        self._connection.close()
