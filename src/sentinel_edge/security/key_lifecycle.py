from __future__ import annotations

import base64
import json
import sqlite3
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sentinel_edge.security.digests import canonical_json_bytes, sha256_bytes


class KeyPurpose(StrEnum):
    AUDIT_SIGNING = "audit_signing"
    SOURCE_SIGNING = "source_signing"
    DEVICE_IDENTITY = "device_identity"
    UPDATE_SIGNING = "update_signing"


class KeyLifecycleAction(StrEnum):
    ACTIVATE = "activate"
    ROTATE = "rotate"
    RETIRE = "retire"
    REVOKE_POLICY = "revoke_policy"
    SUSPECT_COMPROMISE = "suspect_compromise"
    CONFIRM_COMPROMISE = "confirm_compromise"


class KeyState(StrEnum):
    ACTIVE = "active"
    RETIRED = "retired"
    REVOKED_POLICY = "revoked_policy"
    SUSPECTED_COMPROMISE = "suspected_compromise"
    COMPROMISED = "compromised"


_ACTION_TO_STATE = {
    KeyLifecycleAction.ACTIVATE: KeyState.ACTIVE,
    KeyLifecycleAction.ROTATE: KeyState.ACTIVE,
    KeyLifecycleAction.RETIRE: KeyState.RETIRED,
    KeyLifecycleAction.REVOKE_POLICY: KeyState.REVOKED_POLICY,
    KeyLifecycleAction.SUSPECT_COMPROMISE: KeyState.SUSPECTED_COMPROMISE,
    KeyLifecycleAction.CONFIRM_COMPROMISE: KeyState.COMPROMISED,
}


class KeyIdentityRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    identity_id: str
    generation: int = Field(ge=1)
    purpose: KeyPurpose
    public_key_b64: str
    public_key_sha256: str
    policy_version: str
    active_from: datetime
    active_until: datetime | None = None
    state: KeyState = KeyState.ACTIVE
    registered_at: datetime

    @field_validator("identity_id", "policy_version")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("key identity fields must not be blank")
        return value

    @model_validator(mode="after")
    def validate_record(self) -> "KeyIdentityRecord":
        raw = base64.b64decode(self.public_key_b64, validate=True)
        if len(raw) != 32:
            raise ValueError("Ed25519 public key must contain 32 raw bytes")
        if sha256_bytes(raw) != self.public_key_sha256:
            raise ValueError("public key digest mismatch")
        if self.active_until is not None and self.active_until <= self.active_from:
            raise ValueError("active_until must follow active_from")
        return self

    @property
    def key_ref(self) -> str:
        return f"{self.identity_id}:{self.generation}:{self.purpose.value}"


class KeyLifecycleEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: UUID
    identity_id: str
    generation: int = Field(ge=1)
    purpose: KeyPurpose
    action: KeyLifecycleAction
    from_state: KeyState | None
    to_state: KeyState
    effective_at: datetime
    actor: str
    reason: str
    policy_version: str
    compromise_floor_position: int | None = Field(default=None, ge=1)
    payload_sha256: str


class SignatureVerification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    accepted: bool
    status: str
    identity_id: str
    generation: int
    purpose: KeyPurpose
    policy_version: str | None = None
    key_state_at_observation: KeyState | None = None
    current_key_state: KeyState | None = None
    historical: bool
    reason_codes: tuple[str, ...] = ()


class KeyLifecycleRegistry:
    """Append-only public-key lifecycle registry.

    Private keys are never accepted or persisted. Current-use verification fails
    closed for retired, revoked, suspected, or compromised generations. Historical
    verification reports the policy state that applied at the signed time and keeps
    retirement distinct from uncertain compromise.
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
            CREATE TABLE IF NOT EXISTS key_identities (
                identity_id TEXT NOT NULL,
                generation INTEGER NOT NULL,
                purpose TEXT NOT NULL,
                public_key_sha256 TEXT NOT NULL,
                current_state TEXT NOT NULL,
                registered_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                PRIMARY KEY(identity_id,generation,purpose)
            );
            CREATE TABLE IF NOT EXISTS key_lifecycle_events (
                event_id TEXT PRIMARY KEY,
                identity_id TEXT NOT NULL,
                generation INTEGER NOT NULL,
                purpose TEXT NOT NULL,
                action TEXT NOT NULL,
                to_state TEXT NOT NULL,
                effective_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                UNIQUE(identity_id,generation,purpose,effective_at,action)
            );
            CREATE INDEX IF NOT EXISTS idx_key_events_identity_time
                ON key_lifecycle_events(identity_id,generation,purpose,effective_at,event_id);
            """
        )

    @staticmethod
    def public_key_b64(public_key_raw: bytes) -> str:
        if len(public_key_raw) != 32:
            raise ValueError("Ed25519 public key must contain 32 raw bytes")
        return base64.b64encode(public_key_raw).decode("ascii")

    def register(
        self,
        *,
        identity_id: str,
        generation: int,
        purpose: KeyPurpose,
        public_key_raw: bytes,
        policy_version: str,
        actor: str,
        reason: str,
        active_from: datetime | None = None,
        active_until: datetime | None = None,
        registered_at: datetime | None = None,
    ) -> KeyIdentityRecord:
        registered_at = registered_at or datetime.now(timezone.utc)
        active_from = active_from or registered_at
        record = KeyIdentityRecord(
            identity_id=identity_id,
            generation=generation,
            purpose=purpose,
            public_key_b64=self.public_key_b64(public_key_raw),
            public_key_sha256=sha256_bytes(public_key_raw),
            policy_version=policy_version,
            active_from=active_from,
            active_until=active_until,
            state=KeyState.ACTIVE,
            registered_at=registered_at,
        )
        key = (identity_id, generation, purpose.value)
        with self._lock, self._connection:
            existing = self._connection.execute(
                "SELECT payload_json FROM key_identities WHERE identity_id=? AND generation=? AND purpose=?", key
            ).fetchone()
            if existing is not None:
                observed = KeyIdentityRecord.model_validate(json.loads(existing[0]))
                if observed != record:
                    raise ValueError("key identity conflict")
                return observed
            prior_active = self._connection.execute(
                "SELECT generation FROM key_identities WHERE identity_id=? AND purpose=? AND current_state=? ORDER BY generation DESC",
                (identity_id, purpose.value, KeyState.ACTIVE.value),
            ).fetchall()
            if prior_active and generation <= max(int(row[0]) for row in prior_active):
                raise ValueError("new key generation must be greater than the active generation")
            self._connection.execute(
                "INSERT INTO key_identities(identity_id,generation,purpose,public_key_sha256,current_state,registered_at,payload_json) VALUES (?,?,?,?,?,?,?)",
                (*key, record.public_key_sha256, record.state.value, registered_at.isoformat(), record.model_dump_json()),
            )
            action = KeyLifecycleAction.ROTATE if prior_active else KeyLifecycleAction.ACTIVATE
            self._append_event(
                identity_id=identity_id,
                generation=generation,
                purpose=purpose,
                action=action,
                from_state=None,
                to_state=KeyState.ACTIVE,
                effective_at=active_from,
                actor=actor,
                reason=reason,
                policy_version=policy_version,
            )
            for row in prior_active:
                self._transition_locked(
                    identity_id=identity_id,
                    generation=int(row[0]),
                    purpose=purpose,
                    action=KeyLifecycleAction.RETIRE,
                    effective_at=active_from,
                    actor=actor,
                    reason=f"superseded_by_generation_{generation}",
                    policy_version=policy_version,
                    compromise_floor_position=None,
                )
        return record

    def _append_event(
        self,
        *,
        identity_id: str,
        generation: int,
        purpose: KeyPurpose,
        action: KeyLifecycleAction,
        from_state: KeyState | None,
        to_state: KeyState,
        effective_at: datetime,
        actor: str,
        reason: str,
        policy_version: str,
        compromise_floor_position: int | None = None,
    ) -> KeyLifecycleEvent:
        if not actor.strip() or not reason.strip() or not policy_version.strip():
            raise ValueError("key lifecycle governance fields must not be blank")
        base: dict[str, Any] = {
            "identity_id": identity_id,
            "generation": generation,
            "purpose": purpose.value,
            "action": action.value,
            "from_state": from_state.value if from_state else None,
            "to_state": to_state.value,
            "effective_at": effective_at.isoformat(),
            "actor": actor,
            "reason": reason,
            "policy_version": policy_version,
            "compromise_floor_position": compromise_floor_position,
        }
        payload_sha256 = sha256_bytes(canonical_json_bytes(base))
        event_id = uuid5(NAMESPACE_URL, f"sentinel-key-lifecycle:{payload_sha256}")
        event = KeyLifecycleEvent(
            event_id=event_id,
            identity_id=identity_id,
            generation=generation,
            purpose=purpose,
            action=action,
            from_state=from_state,
            to_state=to_state,
            effective_at=effective_at,
            actor=actor,
            reason=reason,
            policy_version=policy_version,
            compromise_floor_position=compromise_floor_position,
            payload_sha256=payload_sha256,
        )
        self._connection.execute(
            "INSERT OR IGNORE INTO key_lifecycle_events(event_id,identity_id,generation,purpose,action,to_state,effective_at,payload_json) VALUES (?,?,?,?,?,?,?,?)",
            (
                str(event.event_id), identity_id, generation, purpose.value, action.value, to_state.value,
                effective_at.isoformat(), event.model_dump_json(),
            ),
        )
        return event

    def _load(self, identity_id: str, generation: int, purpose: KeyPurpose) -> KeyIdentityRecord:
        row = self._connection.execute(
            "SELECT payload_json,current_state FROM key_identities WHERE identity_id=? AND generation=? AND purpose=?",
            (identity_id, generation, purpose.value),
        ).fetchone()
        if row is None:
            raise KeyError(f"{identity_id}:{generation}:{purpose.value}")
        return KeyIdentityRecord.model_validate(json.loads(row[0])).model_copy(update={"state": KeyState(row[1])})

    def _transition_locked(
        self,
        *,
        identity_id: str,
        generation: int,
        purpose: KeyPurpose,
        action: KeyLifecycleAction,
        effective_at: datetime,
        actor: str,
        reason: str,
        policy_version: str,
        compromise_floor_position: int | None,
    ) -> KeyLifecycleEvent:
        current = self._load(identity_id, generation, purpose)
        to_state = _ACTION_TO_STATE[action]
        if action in {KeyLifecycleAction.ACTIVATE, KeyLifecycleAction.ROTATE} and current.state is KeyState.COMPROMISED:
            raise ValueError("a compromised generation cannot be reactivated")
        event = self._append_event(
            identity_id=identity_id,
            generation=generation,
            purpose=purpose,
            action=action,
            from_state=current.state,
            to_state=to_state,
            effective_at=effective_at,
            actor=actor,
            reason=reason,
            policy_version=policy_version,
            compromise_floor_position=compromise_floor_position,
        )
        self._connection.execute(
            "UPDATE key_identities SET current_state=? WHERE identity_id=? AND generation=? AND purpose=?",
            (to_state.value, identity_id, generation, purpose.value),
        )
        return event

    def transition(
        self,
        *,
        identity_id: str,
        generation: int,
        purpose: KeyPurpose,
        action: KeyLifecycleAction,
        actor: str,
        reason: str,
        policy_version: str,
        effective_at: datetime | None = None,
        compromise_floor_position: int | None = None,
    ) -> KeyLifecycleEvent:
        effective_at = effective_at or datetime.now(timezone.utc)
        if action in {KeyLifecycleAction.SUSPECT_COMPROMISE, KeyLifecycleAction.CONFIRM_COMPROMISE}:
            # A missing floor is allowed and intentionally produces indeterminate historical verification.
            pass
        elif compromise_floor_position is not None:
            raise ValueError("compromise floor is valid only for compromise lifecycle actions")
        with self._lock, self._connection:
            return self._transition_locked(
                identity_id=identity_id,
                generation=generation,
                purpose=purpose,
                action=action,
                effective_at=effective_at,
                actor=actor,
                reason=reason,
                policy_version=policy_version,
                compromise_floor_position=compromise_floor_position,
            )

    def records(self, *, purpose: KeyPurpose | None = None) -> tuple[KeyIdentityRecord, ...]:
        if purpose is None:
            rows = self._connection.execute(
                "SELECT payload_json,current_state FROM key_identities ORDER BY purpose,identity_id,generation"
            ).fetchall()
        else:
            rows = self._connection.execute(
                "SELECT payload_json,current_state FROM key_identities WHERE purpose=? ORDER BY identity_id,generation",
                (purpose.value,),
            ).fetchall()
        return tuple(
            KeyIdentityRecord.model_validate(json.loads(row[0])).model_copy(update={"state": KeyState(row[1])})
            for row in rows
        )

    def events(
        self, *, identity_id: str | None = None, generation: int | None = None, purpose: KeyPurpose | None = None
    ) -> tuple[KeyLifecycleEvent, ...]:
        query = "SELECT payload_json FROM key_lifecycle_events WHERE 1=1"
        params: list[Any] = []
        if identity_id is not None:
            query += " AND identity_id=?"
            params.append(identity_id)
        if generation is not None:
            query += " AND generation=?"
            params.append(generation)
        if purpose is not None:
            query += " AND purpose=?"
            params.append(purpose.value)
        query += " ORDER BY effective_at,event_id"
        rows = self._connection.execute(query, tuple(params)).fetchall()
        return tuple(KeyLifecycleEvent.model_validate(json.loads(row[0])) for row in rows)

    def _state_at(
        self, identity_id: str, generation: int, purpose: KeyPurpose, observed_at: datetime
    ) -> tuple[KeyState | None, KeyLifecycleEvent | None]:
        events = [
            event for event in self.events(identity_id=identity_id, generation=generation, purpose=purpose)
            if event.effective_at <= observed_at
        ]
        if not events:
            return None, None
        return events[-1].to_state, events[-1]

    def signing_allowed(
        self, *, identity_id: str, generation: int, purpose: KeyPurpose, at: datetime | None = None
    ) -> KeyIdentityRecord:
        at = at or datetime.now(timezone.utc)
        record = self._load(identity_id, generation, purpose)
        state_at, _ = self._state_at(identity_id, generation, purpose, at)
        if state_at is not KeyState.ACTIVE or record.state is not KeyState.ACTIVE:
            raise PermissionError("key generation is not active for new signatures")
        if at < record.active_from or (record.active_until is not None and at >= record.active_until):
            raise PermissionError("key generation is outside its validity window")
        return record

    def verify(
        self,
        *,
        identity_id: str,
        generation: int,
        purpose: KeyPurpose,
        message: bytes,
        signature_b64: str,
        observed_at: datetime,
        accepted_at: datetime | None = None,
        historical: bool = False,
        authority_position: int | None = None,
    ) -> SignatureVerification:
        accepted_at = accepted_at or datetime.now(timezone.utc)
        try:
            record = self._load(identity_id, generation, purpose)
        except KeyError:
            return SignatureVerification(
                accepted=False, status="unknown_signer", identity_id=identity_id, generation=generation,
                purpose=purpose, historical=historical, reason_codes=("identity_generation_not_registered",),
            )
        try:
            signature = base64.b64decode(signature_b64, validate=True)
            Ed25519PublicKey.from_public_bytes(base64.b64decode(record.public_key_b64)).verify(signature, message)
        except (ValueError, InvalidSignature):
            return SignatureVerification(
                accepted=False, status="invalid_signature", identity_id=identity_id, generation=generation,
                purpose=purpose, policy_version=record.policy_version, current_key_state=record.state,
                historical=historical, reason_codes=("ed25519_verification_failed",),
            )
        state_at, event_at = self._state_at(identity_id, generation, purpose, observed_at)
        if state_at is None or observed_at < record.active_from or (
            record.active_until is not None and observed_at >= record.active_until
        ):
            return SignatureVerification(
                accepted=False, status="outside_key_validity", identity_id=identity_id, generation=generation,
                purpose=purpose, policy_version=record.policy_version, current_key_state=record.state,
                historical=historical, reason_codes=("signature_time_not_covered_by_key_generation",),
            )
        if not historical:
            try:
                self.signing_allowed(identity_id=identity_id, generation=generation, purpose=purpose, at=accepted_at)
            except PermissionError:
                return SignatureVerification(
                    accepted=False, status="key_not_accepted_for_new_evidence", identity_id=identity_id,
                    generation=generation, purpose=purpose, policy_version=record.policy_version,
                    key_state_at_observation=state_at, current_key_state=record.state, historical=False,
                    reason_codes=("current_key_lifecycle_blocks_new_acceptance",),
                )
            return SignatureVerification(
                accepted=True, status="valid_active", identity_id=identity_id, generation=generation,
                purpose=purpose, policy_version=record.policy_version, key_state_at_observation=state_at,
                current_key_state=record.state, historical=False,
            )

        later_events = [
            event for event in self.events(identity_id=identity_id, generation=generation, purpose=purpose)
            if event.effective_at > observed_at
        ]
        compromise = next(
            (event for event in later_events if event.action in {
                KeyLifecycleAction.SUSPECT_COMPROMISE, KeyLifecycleAction.CONFIRM_COMPROMISE
            }),
            None,
        )
        if compromise is not None:
            if compromise.compromise_floor_position is None:
                return SignatureVerification(
                    accepted=False, status="indeterminate_compromise_interval", identity_id=identity_id,
                    generation=generation, purpose=purpose, policy_version=event_at.policy_version if event_at else record.policy_version,
                    key_state_at_observation=state_at, current_key_state=record.state, historical=True,
                    reason_codes=("compromise_start_unknown",),
                )
            if authority_position is None or authority_position >= compromise.compromise_floor_position:
                return SignatureVerification(
                    accepted=False, status="not_validated_after_compromise_floor", identity_id=identity_id,
                    generation=generation, purpose=purpose, policy_version=event_at.policy_version if event_at else record.policy_version,
                    key_state_at_observation=state_at, current_key_state=record.state, historical=True,
                    reason_codes=("checkpoint_at_or_after_compromise_floor",),
                )
            return SignatureVerification(
                accepted=True, status="valid_before_compromise_floor", identity_id=identity_id,
                generation=generation, purpose=purpose, policy_version=event_at.policy_version if event_at else record.policy_version,
                key_state_at_observation=state_at, current_key_state=record.state, historical=True,
                reason_codes=("checkpoint_precedes_known_compromise_floor",),
            )
        if record.state is KeyState.RETIRED:
            status = "historically_valid_retired"
        elif record.state is KeyState.REVOKED_POLICY:
            status = "historically_valid_before_policy_revocation"
        else:
            status = "valid_active"
        return SignatureVerification(
            accepted=True, status=status, identity_id=identity_id, generation=generation, purpose=purpose,
            policy_version=event_at.policy_version if event_at else record.policy_version,
            key_state_at_observation=state_at, current_key_state=record.state, historical=True,
        )

    def close(self) -> None:
        self._connection.close()
