from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from pathlib import Path
from threading import RLock
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sentinel_edge.security.digests import canonical_json_bytes, sha256_bytes


class SecretState(StrEnum):
    STAGED = "staged"
    ACTIVE = "active"
    OVERLAP = "overlap"
    REVOKED = "revoked"
    COMPROMISED = "compromised"
    EXPIRED = "expired"
    UNAVAILABLE = "unavailable"


class SecretReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    reference_id: str
    version: int = Field(ge=1)
    owner_module: str
    purpose: str
    policy_version: str
    valid_from: datetime
    valid_until: datetime
    state: SecretState = SecretState.STAGED

    @field_validator("reference_id", "owner_module", "purpose", "policy_version")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("secret reference fields must not be blank")
        return value

    @model_validator(mode="after")
    def validate_window(self) -> "SecretReference":
        if self.valid_until <= self.valid_from:
            raise ValueError("secret validity window is invalid")
        return self

    @property
    def key(self) -> str:
        return f"{self.reference_id}@{self.version}"


class SecretRotationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    reference_id: str
    old_version: int = Field(ge=1)
    new_version: int = Field(ge=1)
    overlap_starts_at: datetime
    cutover_at: datetime
    overlap_ends_at: datetime
    maximum_overlap_seconds: int = Field(gt=0, le=86400)

    @model_validator(mode="after")
    def validate_plan(self) -> "SecretRotationPlan":
        if self.new_version <= self.old_version:
            raise ValueError("new secret version must increase")
        if not self.overlap_starts_at < self.cutover_at <= self.overlap_ends_at:
            raise ValueError("secret rotation timeline is invalid")
        if (self.overlap_ends_at - self.overlap_starts_at).total_seconds() > self.maximum_overlap_seconds:
            raise ValueError("secret overlap exceeds the declared bound")
        return self


class SecretMetadataSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True)

    schema_: str = Field(default="sentinel-edge-secret-metadata/1.0", alias="schema")
    reference_id: str
    version: int
    owner_module: str
    purpose: str
    policy_version: str
    state: SecretState
    valid_from: datetime
    valid_until: datetime
    metadata_sha256: str


@dataclass(frozen=True)
class SecretHandle:
    handle_id: UUID
    reference_key: str
    owner_module: str
    purpose: str
    issued_at: datetime
    expires_at: datetime
    generation_epoch: int


class SecretRegistry:
    """Metadata-persistent secret registry; secret bytes remain only in the owning process memory."""

    def __init__(self, path: str | Path = ":memory:", *, maximum_handle_seconds: int = 300) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.maximum_handle_seconds = maximum_handle_seconds
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=FULL")
        self._connection.row_factory = sqlite3.Row
        self._lock = RLock()
        self._values: dict[str, bytes] = {}
        self._handles: dict[UUID, SecretHandle] = {}
        self._generation_epoch = 1
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS secret_references (
                secret_key TEXT PRIMARY KEY,
                reference_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                owner_module TEXT NOT NULL,
                purpose TEXT NOT NULL,
                policy_version TEXT NOT NULL,
                state TEXT NOT NULL,
                valid_from TEXT NOT NULL,
                valid_until TEXT NOT NULL,
                metadata_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                UNIQUE(reference_id,version)
            );
            CREATE TABLE IF NOT EXISTS secret_rotations (
                plan_id TEXT PRIMARY KEY,
                reference_id TEXT NOT NULL,
                old_version INTEGER NOT NULL,
                new_version INTEGER NOT NULL,
                overlap_starts_at TEXT NOT NULL,
                cutover_at TEXT NOT NULL,
                overlap_ends_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS secret_events (
                event_id TEXT PRIMARY KEY,
                reference_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                state TEXT NOT NULL,
                actor TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            """
        )

    @staticmethod
    def _metadata_digest(ref: SecretReference) -> str:
        return sha256_bytes(canonical_json_bytes(ref.model_dump(mode="json")))

    def register(self, reference: SecretReference, value: bytes, *, actor: str = "secret-owner") -> SecretMetadataSnapshot:
        if not value:
            raise ValueError("secret value must not be empty")
        digest = self._metadata_digest(reference)
        with self._lock, self._connection:
            row = self._connection.execute(
                "SELECT metadata_sha256 FROM secret_references WHERE secret_key=?", (reference.key,)
            ).fetchone()
            if row is not None and row["metadata_sha256"] != digest:
                raise ValueError("secret reference identity conflict")
            self._connection.execute(
                """INSERT OR IGNORE INTO secret_references(
                   secret_key,reference_id,version,owner_module,purpose,policy_version,state,valid_from,valid_until,metadata_sha256,payload_json
                   ) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    reference.key, reference.reference_id, reference.version, reference.owner_module, reference.purpose,
                    reference.policy_version, reference.state.value, reference.valid_from.isoformat(), reference.valid_until.isoformat(),
                    digest, reference.model_dump_json(),
                ),
            )
            self._values[reference.key] = bytes(value)
            self._record_event(reference, actor=actor, reason="registered")
        return self.snapshot(reference.key)

    def _record_event(self, ref: SecretReference, *, actor: str, reason: str, created_at: datetime | None = None) -> None:
        created_at = created_at or datetime.now(timezone.utc)
        payload = {
            "reference_id": ref.reference_id,
            "version": ref.version,
            "state": ref.state.value,
            "actor": actor,
            "reason": reason,
            "created_at": created_at.isoformat(),
        }
        event_id = uuid5(NAMESPACE_URL, f"sentinel-secret-event:{sha256_bytes(canonical_json_bytes(payload))}")
        self._connection.execute(
            """INSERT OR IGNORE INTO secret_events(
               event_id,reference_id,version,state,actor,reason,created_at,payload_json
               ) VALUES (?,?,?,?,?,?,?,?)""",
            (str(event_id), ref.reference_id, ref.version, ref.state.value, actor, reason, created_at.isoformat(), json.dumps(payload, sort_keys=True)),
        )

    def _load(self, key: str) -> SecretReference:
        row = self._connection.execute("SELECT payload_json FROM secret_references WHERE secret_key=?", (key,)).fetchone()
        if row is None:
            raise KeyError(key)
        return SecretReference.model_validate(json.loads(row[0]))

    def snapshot(self, key: str) -> SecretMetadataSnapshot:
        ref = self._load(key)
        return SecretMetadataSnapshot(
            reference_id=ref.reference_id,
            version=ref.version,
            owner_module=ref.owner_module,
            purpose=ref.purpose,
            policy_version=ref.policy_version,
            state=ref.state,
            valid_from=ref.valid_from,
            valid_until=ref.valid_until,
            metadata_sha256=self._metadata_digest(ref),
        )

    def metadata(self) -> tuple[SecretMetadataSnapshot, ...]:
        rows = self._connection.execute("SELECT secret_key FROM secret_references ORDER BY reference_id,version").fetchall()
        return tuple(self.snapshot(row[0]) for row in rows)

    def transition(self, key: str, *, state: SecretState, actor: str, reason: str) -> SecretMetadataSnapshot:
        ref = self._load(key).model_copy(update={"state": state})
        digest = self._metadata_digest(ref)
        with self._lock, self._connection:
            self._connection.execute(
                "UPDATE secret_references SET state=?,metadata_sha256=?,payload_json=? WHERE secret_key=?",
                (state.value, digest, ref.model_dump_json(), key),
            )
            if state in {SecretState.REVOKED, SecretState.COMPROMISED, SecretState.EXPIRED, SecretState.UNAVAILABLE}:
                self._values.pop(key, None)
                self._generation_epoch += 1
                self._handles.clear()
            self._record_event(ref, actor=actor, reason=reason)
        return self.snapshot(key)

    def plan_rotation(self, plan: SecretRotationPlan, *, actor: str = "secret-owner") -> str:
        old = self._load(f"{plan.reference_id}@{plan.old_version}")
        new = self._load(f"{plan.reference_id}@{plan.new_version}")
        if old.owner_module != new.owner_module or old.purpose != new.purpose:
            raise ValueError("rotation versions must preserve owner and purpose")
        plan_id = str(uuid5(NAMESPACE_URL, f"sentinel-secret-rotation:{sha256_bytes(canonical_json_bytes(plan.model_dump(mode='json')))}"))
        with self._lock, self._connection:
            self._connection.execute(
                """INSERT OR IGNORE INTO secret_rotations(
                   plan_id,reference_id,old_version,new_version,overlap_starts_at,cutover_at,overlap_ends_at,payload_json
                   ) VALUES (?,?,?,?,?,?,?,?)""",
                (
                    plan_id, plan.reference_id, plan.old_version, plan.new_version, plan.overlap_starts_at.isoformat(),
                    plan.cutover_at.isoformat(), plan.overlap_ends_at.isoformat(), plan.model_dump_json(),
                ),
            )
        return plan_id

    def apply_rotation(self, plan_id: str, *, now: datetime | None = None, actor: str = "secret-owner") -> dict[str, str]:
        now = now or datetime.now(timezone.utc)
        row = self._connection.execute("SELECT payload_json FROM secret_rotations WHERE plan_id=?", (plan_id,)).fetchone()
        if row is None:
            raise KeyError(plan_id)
        plan = SecretRotationPlan.model_validate(json.loads(row[0]))
        old_key = f"{plan.reference_id}@{plan.old_version}"
        new_key = f"{plan.reference_id}@{plan.new_version}"
        if now < plan.overlap_starts_at:
            old_state, new_state = SecretState.ACTIVE, SecretState.STAGED
        elif now < plan.cutover_at:
            old_state, new_state = SecretState.OVERLAP, SecretState.OVERLAP
        elif now < plan.overlap_ends_at:
            old_state, new_state = SecretState.OVERLAP, SecretState.ACTIVE
        else:
            old_state, new_state = SecretState.REVOKED, SecretState.ACTIVE
        self.transition(old_key, state=old_state, actor=actor, reason=f"rotation:{plan_id}")
        self.transition(new_key, state=new_state, actor=actor, reason=f"rotation:{plan_id}")
        self._generation_epoch += 1
        self._handles.clear()
        return {"old": old_state.value, "new": new_state.value}

    def resolve(
        self,
        key: str,
        *,
        requesting_module: str,
        purpose: str,
        now: datetime | None = None,
        lifetime_seconds: int = 60,
    ) -> SecretHandle:
        now = now or datetime.now(timezone.utc)
        if lifetime_seconds <= 0 or lifetime_seconds > self.maximum_handle_seconds:
            raise ValueError("secret handle lifetime is outside policy")
        ref = self._load(key)
        if requesting_module != ref.owner_module or purpose != ref.purpose:
            raise PermissionError("module or purpose is not authorized for this secret")
        if not ref.valid_from <= now < ref.valid_until:
            raise PermissionError("secret reference is outside its validity window")
        if ref.state not in {SecretState.ACTIVE, SecretState.OVERLAP}:
            raise PermissionError(f"secret reference is not available: {ref.state.value}")
        if key not in self._values:
            raise PermissionError("secret bytes are unavailable in this process")
        handle = SecretHandle(
            handle_id=uuid4(),
            reference_key=key,
            owner_module=requesting_module,
            purpose=purpose,
            issued_at=now,
            expires_at=min(now + timedelta(seconds=lifetime_seconds), ref.valid_until),
            generation_epoch=self._generation_epoch,
        )
        self._handles[handle.handle_id] = handle
        return handle

    def read(self, handle: SecretHandle, *, now: datetime | None = None) -> bytes:
        now = now or datetime.now(timezone.utc)
        current = self._handles.get(handle.handle_id)
        if current != handle or handle.generation_epoch != self._generation_epoch:
            raise PermissionError("secret handle is stale or unknown")
        if now >= handle.expires_at:
            self._handles.pop(handle.handle_id, None)
            raise PermissionError("secret handle expired")
        value = self._values.get(handle.reference_key)
        if value is None:
            raise PermissionError("secret bytes are unavailable")
        return bytes(value)

    def capability_state(self, key: str, *, now: datetime | None = None) -> dict[str, object]:
        now = now or datetime.now(timezone.utc)
        ref = self._load(key)
        if now >= ref.valid_until:
            state = "degraded"
            reasons = ("credential_expired",)
        elif ref.state in {SecretState.REVOKED, SecretState.COMPROMISED, SecretState.UNAVAILABLE, SecretState.EXPIRED}:
            state = "degraded"
            reasons = (f"credential_{ref.state.value}",)
        elif key not in self._values:
            state = "degraded"
            reasons = ("credential_bytes_unavailable",)
        else:
            state = "healthy"
            reasons = ()
        return {
            "reference": key,
            "owner_module": ref.owner_module,
            "purpose": ref.purpose,
            "state": state,
            "reason_codes": reasons,
            "local_physical_monitoring_affected": False,
        }

    def scan_for_secret(self, root: str | Path, secret: bytes) -> tuple[str, ...]:
        if not secret:
            raise ValueError("secret scan value must not be empty")
        findings: list[str] = []
        root = Path(root)
        for path in root.rglob("*"):
            if not path.is_file() or path.resolve() == Path(self.path).resolve():
                continue
            try:
                data = path.read_bytes()
            except OSError:
                continue
            if secret in data:
                findings.append(path.relative_to(root).as_posix())
        return tuple(sorted(findings))

    def close(self) -> None:
        self._connection.close()
