from __future__ import annotations

import base64
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Iterable
from uuid import NAMESPACE_URL, UUID, uuid5

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel_edge.domain.models import AuthorityMutation
from sentinel_edge.security.digests import canonical_json_bytes, sha256_bytes
from sentinel_edge.security.key_lifecycle import KeyLifecycleRegistry, KeyPurpose, SignatureVerification


NON_FORENSIC_WORDING = (
    "Tamper-evident local journal checkpoint only. It does not prove that a sensor, "
    "external report, physical event, or operator statement was truthful."
)


def _entry_payload(entry: AuthorityMutation) -> dict[str, Any]:
    return {
        "position": entry.position,
        "kind": entry.kind.value,
        "entity_id": entry.entity_id,
        "accepted_at": entry.accepted_at.isoformat(),
        "payload_sha256": sha256_bytes(canonical_json_bytes(entry.payload)),
    }


def authority_chain(entries: Iterable[AuthorityMutation]) -> tuple[str, tuple[dict[str, Any], ...]]:
    ordered = tuple(sorted(entries, key=lambda item: item.position))
    if not ordered:
        raise ValueError("audit checkpoint requires at least one authority mutation")
    expected = list(range(1, ordered[-1].position + 1))
    observed = [item.position for item in ordered]
    if observed != expected:
        raise ValueError("authority checkpoint prefix must be contiguous from position 1")
    previous = "0" * 64
    transcript: list[dict[str, Any]] = []
    for entry in ordered:
        payload = _entry_payload(entry)
        digest = sha256_bytes(previous.encode("ascii") + canonical_json_bytes(payload))
        transcript.append({**payload, "predecessor_sha256": previous, "entry_chain_sha256": digest})
        previous = digest
    return previous, tuple(transcript)


class AuditCheckpoint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_id: str = "sentinel-edge-audit-checkpoint/1.0"
    checkpoint_id: UUID
    created_at: datetime
    authority_epoch_id: str
    first_position: int = Field(ge=1)
    head_position: int = Field(ge=1)
    entry_count: int = Field(ge=1)
    chain_root_sha256: str
    transcript_sha256: str
    signer_identity_id: str
    signer_generation: int = Field(ge=1)
    signer_policy_version: str
    verification_policy: str
    signer_state_at_signing: str
    non_forensic_wording: str = NON_FORENSIC_WORDING
    payload_sha256: str
    signature_b64: str

    @model_validator(mode="after")
    def validate_checkpoint(self) -> "AuditCheckpoint":
        if self.first_position != 1 or self.entry_count != self.head_position:
            raise ValueError("audit checkpoint must close a contiguous journal prefix from position 1")
        if "does not prove" not in self.non_forensic_wording.lower():
            raise ValueError("audit checkpoint must retain non-forensic wording")
        return self


class AuditCheckpointVerification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    valid: bool
    checkpoint_id: UUID
    head_position: int
    chain_valid: bool
    signature: SignatureVerification
    failures: tuple[str, ...]
    non_forensic_wording: str


class AuditCheckpointService:
    def __init__(
        self,
        key_registry: KeyLifecycleRegistry,
        path: str | Path = ":memory:",
    ) -> None:
        self.key_registry = key_registry
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
            CREATE TABLE IF NOT EXISTS audit_checkpoints (
                checkpoint_id TEXT PRIMARY KEY,
                head_position INTEGER NOT NULL,
                signer_identity_id TEXT NOT NULL,
                signer_generation INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                UNIQUE(head_position,signer_identity_id,signer_generation)
            );
            """
        )

    @staticmethod
    def _signable_payload(data: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in data.items() if key not in {"payload_sha256", "signature_b64"}}

    def create(
        self,
        *,
        entries: Iterable[AuthorityMutation],
        authority_epoch_id: str,
        signer_identity_id: str,
        signer_generation: int,
        private_key_raw: bytes,
        created_at: datetime | None = None,
        verification_policy: str = "audit-checkpoint-policy-v1",
    ) -> AuditCheckpoint:
        created_at = created_at or datetime.now(timezone.utc)
        record = self.key_registry.signing_allowed(
            identity_id=signer_identity_id,
            generation=signer_generation,
            purpose=KeyPurpose.AUDIT_SIGNING,
            at=created_at,
        )
        ordered = tuple(sorted(entries, key=lambda item: item.position))
        root, transcript = authority_chain(ordered)
        transcript_sha256 = sha256_bytes(canonical_json_bytes(transcript))
        seed = {
            "authority_epoch_id": authority_epoch_id,
            "head_position": ordered[-1].position,
            "chain_root_sha256": root,
            "signer_identity_id": signer_identity_id,
            "signer_generation": signer_generation,
            "created_at": created_at.isoformat().replace("+00:00", "Z"),
        }
        checkpoint_id = uuid5(NAMESPACE_URL, f"sentinel-audit-checkpoint:{sha256_bytes(canonical_json_bytes(seed))}")
        unsigned = {
            "schema_id": "sentinel-edge-audit-checkpoint/1.0",
            "checkpoint_id": str(checkpoint_id),
            "created_at": created_at.isoformat().replace("+00:00", "Z"),
            "authority_epoch_id": authority_epoch_id,
            "first_position": 1,
            "head_position": ordered[-1].position,
            "entry_count": len(ordered),
            "chain_root_sha256": root,
            "transcript_sha256": transcript_sha256,
            "signer_identity_id": signer_identity_id,
            "signer_generation": signer_generation,
            "signer_policy_version": record.policy_version,
            "verification_policy": verification_policy,
            "signer_state_at_signing": record.state.value,
            "non_forensic_wording": NON_FORENSIC_WORDING,
        }
        payload_sha256 = sha256_bytes(canonical_json_bytes(unsigned))
        if len(private_key_raw) != 32:
            raise ValueError("Ed25519 private key must contain 32 raw bytes")
        signature_b64 = base64.b64encode(
            Ed25519PrivateKey.from_private_bytes(private_key_raw).sign(canonical_json_bytes(unsigned))
        ).decode("ascii")
        checkpoint = AuditCheckpoint.model_validate({
            **unsigned,
            "payload_sha256": payload_sha256,
            "signature_b64": signature_b64,
        })
        with self._lock, self._connection:
            existing = self._connection.execute(
                "SELECT payload_json FROM audit_checkpoints WHERE checkpoint_id=?", (str(checkpoint_id),)
            ).fetchone()
            if existing is not None:
                observed = AuditCheckpoint.model_validate(json.loads(existing[0]))
                if observed != checkpoint:
                    raise ValueError("audit checkpoint identity conflict")
                return observed
            self._connection.execute(
                "INSERT INTO audit_checkpoints(checkpoint_id,head_position,signer_identity_id,signer_generation,created_at,payload_sha256,payload_json) VALUES (?,?,?,?,?,?,?)",
                (
                    str(checkpoint_id), checkpoint.head_position, signer_identity_id, signer_generation,
                    created_at.isoformat(), payload_sha256, checkpoint.model_dump_json(),
                ),
            )
        return checkpoint

    def verify(
        self,
        checkpoint: AuditCheckpoint | dict[str, Any],
        *,
        entries: Iterable[AuthorityMutation],
    ) -> AuditCheckpointVerification:
        checkpoint = checkpoint if isinstance(checkpoint, AuditCheckpoint) else AuditCheckpoint.model_validate(checkpoint)
        failures: list[str] = []
        ordered_all = tuple(sorted(entries, key=lambda item: item.position))
        prefix = tuple(item for item in ordered_all if item.position <= checkpoint.head_position)
        chain_valid = False
        try:
            root, transcript = authority_chain(prefix)
            if len(prefix) != checkpoint.entry_count:
                failures.append("journal_prefix_truncated")
            if root != checkpoint.chain_root_sha256:
                failures.append("journal_prefix_substituted")
            if sha256_bytes(canonical_json_bytes(transcript)) != checkpoint.transcript_sha256:
                failures.append("journal_transcript_digest_mismatch")
            chain_valid = not failures
        except ValueError as exc:
            failures.append(f"journal_prefix_invalid:{exc}")
        raw = checkpoint.model_dump(mode="json")
        unsigned = self._signable_payload(raw)
        observed_payload_sha256 = sha256_bytes(canonical_json_bytes(unsigned))
        if observed_payload_sha256 != checkpoint.payload_sha256:
            failures.append("checkpoint_payload_digest_mismatch")
        signature = self.key_registry.verify(
            identity_id=checkpoint.signer_identity_id,
            generation=checkpoint.signer_generation,
            purpose=KeyPurpose.AUDIT_SIGNING,
            message=canonical_json_bytes(unsigned),
            signature_b64=checkpoint.signature_b64,
            observed_at=checkpoint.created_at,
            accepted_at=datetime.now(timezone.utc),
            historical=True,
            authority_position=checkpoint.head_position,
        )
        if not signature.accepted:
            failures.append(f"signature:{signature.status}")
        if checkpoint.non_forensic_wording != NON_FORENSIC_WORDING:
            failures.append("non_forensic_wording_changed")
        return AuditCheckpointVerification(
            valid=not failures,
            checkpoint_id=checkpoint.checkpoint_id,
            head_position=checkpoint.head_position,
            chain_valid=chain_valid,
            signature=signature,
            failures=tuple(sorted(failures)),
            non_forensic_wording=checkpoint.non_forensic_wording,
        )

    def checkpoints(self) -> tuple[AuditCheckpoint, ...]:
        rows = self._connection.execute(
            "SELECT payload_json FROM audit_checkpoints ORDER BY head_position,created_at,checkpoint_id"
        ).fetchall()
        return tuple(AuditCheckpoint.model_validate(json.loads(row[0])) for row in rows)

    def close(self) -> None:
        self._connection.close()
