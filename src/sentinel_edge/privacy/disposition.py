from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from pathlib import Path
from threading import RLock
from typing import Any, Callable
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sentinel_edge.domain.models import EvidenceContentState
from sentinel_edge.security import canonical_json_bytes, sha256_bytes


class DispositionAction(StrEnum):
    ERASE = "erase"
    RESTRICT = "restrict"
    CONSENT_WITHDRAWAL = "consent_withdrawal"
    CORRECT = "correct"


class DispositionRequestStatus(StrEnum):
    RESTRICTED = "restricted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    RETAINED_EXCEPTION = "retained_exception"
    EXTERNAL_RECIPIENT_PENDING = "external_recipient_pending"
    FAILED = "failed"




class RecipientReconciliationState(StrEnum):
    ACKNOWLEDGED = "acknowledged"
    RETRY_SCHEDULED = "retry_scheduled"
    EXHAUSTED = "exhausted"
    DEADLINE_EXPIRED = "deadline_expired"
    ALREADY_ACKNOWLEDGED = "already_acknowledged"
    NOT_DUE = "not_due"


class ExternalRecipientReconciliationAttempt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    attempt_id: UUID
    request_id: UUID
    node_id: UUID
    recipient_digest: str
    attempt_no: int = Field(ge=1)
    state: RecipientReconciliationState
    actor: str
    created_at: datetime
    next_retry_at: datetime | None = None
    response_code: str | None = None
    receipt_sha256: str | None = None
    payload_sha256: str


class ExternalRecipientReconciliationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: UUID
    generated_at: datetime
    attempts: tuple[ExternalRecipientReconciliationAttempt, ...]
    acknowledged: int = Field(ge=0)
    retry_scheduled: int = Field(ge=0)
    exhausted: int = Field(ge=0)
    deadline_expired: int = Field(ge=0)
    pending: int = Field(ge=0)
    complete: bool
    report_sha256: str


class DispositionNodeKind(StrEnum):
    ORIGINAL = "original"
    REDACTION = "redaction"
    THUMBNAIL = "thumbnail"
    OCR = "ocr"
    ASR = "asr"
    EMBEDDING = "embedding"
    SEARCH_INDEX = "search_index"
    CACHE = "cache"
    EXPORT = "export"
    GRANT = "grant"
    LEASE = "lease"
    REPLICA = "replica"
    EXTERNAL_RECIPIENT = "external_recipient"


class DispositionNodeStatus(StrEnum):
    ACTIVE = "active"
    RESTRICTED = "restricted"
    DELETED = "deleted"
    REVOKED = "revoked"
    RETAINED_EXCEPTION = "retained_exception"
    EXTERNAL_PENDING = "external_pending"
    FAILED = "failed"


class DispositionLineageNode(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    node_id: UUID
    evidence_id: UUID
    kind: DispositionNodeKind
    target_ref: str
    parent_node_id: UUID | None = None
    external_recipient_digest: str | None = None
    exception_reason: str | None = None
    exception_expires_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("target_ref")
    @classmethod
    def target_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("disposition target_ref must not be blank")
        return value

    @model_validator(mode="after")
    def validate_node(self) -> "DispositionLineageNode":
        if self.kind is DispositionNodeKind.EXTERNAL_RECIPIENT and not self.external_recipient_digest:
            raise ValueError("external recipient nodes require a recipient digest")
        if self.exception_expires_at is not None and not self.exception_reason:
            raise ValueError("retained exception expiry requires an explicit reason")
        return self


class DispositionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: UUID
    action: DispositionAction
    evidence_ids: tuple[UUID, ...]
    subject_digest: str
    subject_basis: str
    actor: str
    reason: str
    deadline: datetime
    created_at: datetime
    status: DispositionRequestStatus = DispositionRequestStatus.RESTRICTED
    legal_exception_reason: str | None = None
    legal_exception_expires_at: datetime | None = None
    terminal_outcome: str | None = None

    @field_validator("subject_digest")
    @classmethod
    def digest_valid(cls, value: str) -> str:
        if len(value) != 64 or any(c not in "0123456789abcdef" for c in value.lower()):
            raise ValueError("subject_digest must be a lowercase SHA-256")
        return value

    @model_validator(mode="after")
    def validate_request(self) -> "DispositionRequest":
        if not self.evidence_ids:
            raise ValueError("disposition request requires evidence scope")
        if not self.actor.strip() or not self.reason.strip() or not self.subject_basis.strip():
            raise ValueError("disposition request governance fields must not be blank")
        if self.deadline <= self.created_at:
            raise ValueError("disposition deadline must follow creation")
        if self.legal_exception_expires_at is not None and not self.legal_exception_reason:
            raise ValueError("legal exception expiry requires an explicit reason")
        return self


class DispositionNodeResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    node_id: UUID
    evidence_id: UUID
    kind: DispositionNodeKind
    status: DispositionNodeStatus
    target_digest: str
    reason_codes: tuple[str, ...]
    updated_at: datetime
    receipt_sha256: str | None = None


class DispositionReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: UUID
    status: DispositionRequestStatus
    completed: int = Field(ge=0)
    retained_by_exception: int = Field(ge=0)
    external_recipient_pending: int = Field(ge=0)
    failed: int = Field(ge=0)
    restricted: int = Field(ge=0)
    node_results: tuple[DispositionNodeResult, ...]
    subject_digest: str
    deadline: datetime
    terminal_outcome: str | None = None
    generated_at: datetime
    report_sha256: str


class PrivacyDispositionService:
    """Governed, append-only disposition closure over evidence descendants and recipients."""

    def __init__(
        self,
        path: str | Path = ":memory:",
        *,
        authority_recorder: Callable[[str, str, datetime, dict[str, Any]], Any] | None = None,
    ) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=FULL")
        self._connection.execute("PRAGMA busy_timeout=5000")
        self._connection.row_factory = sqlite3.Row
        self._lock = RLock()
        self._authority_recorder = authority_recorder
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS disposition_lineage_nodes (
                node_id TEXT PRIMARY KEY,
                evidence_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                target_ref TEXT NOT NULL,
                parent_node_id TEXT,
                external_recipient_digest TEXT,
                exception_reason TEXT,
                exception_expires_at TEXT,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_disposition_nodes_evidence ON disposition_lineage_nodes(evidence_id,kind);
            CREATE TABLE IF NOT EXISTS disposition_requests (
                request_id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                subject_digest TEXT NOT NULL,
                status TEXT NOT NULL,
                deadline TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS disposition_request_evidence (
                request_id TEXT NOT NULL,
                evidence_id TEXT NOT NULL,
                PRIMARY KEY(request_id,evidence_id)
            );
            CREATE TABLE IF NOT EXISTS disposition_node_events (
                event_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                node_id TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                UNIQUE(request_id,node_id,status)
            );
            CREATE TABLE IF NOT EXISTS disposition_restrictions (
                evidence_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                action TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS consent_blocks (
                subject_digest TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                alternate_basis TEXT
            );
            CREATE TABLE IF NOT EXISTS external_recipient_receipts (
                receipt_id TEXT PRIMARY KEY,
                node_id TEXT NOT NULL,
                recipient_digest TEXT NOT NULL,
                action TEXT NOT NULL,
                actor TEXT NOT NULL,
                created_at TEXT NOT NULL,
                receipt_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS external_recipient_reconciliation_attempts (
                attempt_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                node_id TEXT NOT NULL,
                recipient_digest TEXT NOT NULL,
                attempt_no INTEGER NOT NULL,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL,
                next_retry_at TEXT,
                response_code TEXT,
                receipt_sha256 TEXT,
                payload_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                UNIQUE(request_id,node_id,attempt_no)
            );
            CREATE INDEX IF NOT EXISTS idx_external_reconciliation_due
              ON external_recipient_reconciliation_attempts(request_id,node_id,attempt_no);
            """
        )

    def _authority(self, entity_id: str, created_at: datetime, payload: dict[str, Any]) -> None:
        if self._authority_recorder is not None:
            self._authority_recorder("disposition", entity_id, created_at, payload)

    @staticmethod
    def subject_digest(subject_ref: str) -> str:
        return sha256_bytes(f"sentinel-disposition-subject-v1:{subject_ref}".encode("utf-8"))

    def register_node(
        self,
        *,
        evidence_id: UUID,
        kind: DispositionNodeKind,
        target_ref: str,
        parent_node_id: UUID | None = None,
        external_recipient: str | None = None,
        exception_reason: str | None = None,
        exception_expires_at: datetime | None = None,
        created_at: datetime | None = None,
    ) -> DispositionLineageNode:
        created_at = created_at or datetime.now(timezone.utc)
        recipient_digest = self.subject_digest(external_recipient) if external_recipient else None
        seed = {
            "evidence_id": str(evidence_id),
            "kind": kind.value,
            "target_ref": target_ref,
            "parent_node_id": str(parent_node_id) if parent_node_id else None,
            "recipient_digest": recipient_digest,
        }
        node_id = uuid5(NAMESPACE_URL, f"sentinel-disposition-node:{sha256_bytes(canonical_json_bytes(seed))}")
        node = DispositionLineageNode(
            node_id=node_id,
            evidence_id=evidence_id,
            kind=kind,
            target_ref=target_ref,
            parent_node_id=parent_node_id,
            external_recipient_digest=recipient_digest,
            exception_reason=exception_reason,
            exception_expires_at=exception_expires_at,
            created_at=created_at,
        )
        with self._lock, self._connection:
            row = self._connection.execute("SELECT payload_json FROM disposition_lineage_nodes WHERE node_id=?", (str(node_id),)).fetchone()
            if row is not None:
                existing = DispositionLineageNode.model_validate(json.loads(row[0]))
                if existing != node:
                    raise ValueError("disposition node identity conflict")
                return existing
            self._connection.execute(
                """INSERT INTO disposition_lineage_nodes(
                   node_id,evidence_id,kind,target_ref,parent_node_id,external_recipient_digest,
                   exception_reason,exception_expires_at,created_at,payload_json
                   ) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    str(node_id), str(evidence_id), kind.value, target_ref, str(parent_node_id) if parent_node_id else None,
                    recipient_digest, exception_reason, exception_expires_at.isoformat() if exception_expires_at else None,
                    created_at.isoformat(), node.model_dump_json(),
                ),
            )
        return node

    def nodes(self, evidence_id: UUID | None = None) -> tuple[DispositionLineageNode, ...]:
        if evidence_id is None:
            rows = self._connection.execute("SELECT payload_json FROM disposition_lineage_nodes ORDER BY created_at,node_id").fetchall()
        else:
            rows = self._connection.execute(
                "SELECT payload_json FROM disposition_lineage_nodes WHERE evidence_id=? ORDER BY created_at,node_id",
                (str(evidence_id),),
            ).fetchall()
        return tuple(DispositionLineageNode.model_validate(json.loads(row[0])) for row in rows)

    def create_request(
        self,
        *,
        action: DispositionAction,
        evidence_ids: tuple[UUID, ...],
        subject_ref: str,
        subject_basis: str,
        actor: str,
        reason: str,
        deadline: datetime,
        legal_exception_reason: str | None = None,
        legal_exception_expires_at: datetime | None = None,
        created_at: datetime | None = None,
    ) -> DispositionRequest:
        created_at = created_at or datetime.now(timezone.utc)
        subject_digest = self.subject_digest(subject_ref)
        seed = {
            "action": action.value,
            "evidence_ids": sorted(str(item) for item in evidence_ids),
            "subject_digest": subject_digest,
            "actor": actor,
            "reason": reason,
            "created_at": created_at.isoformat(),
        }
        request_id = uuid5(NAMESPACE_URL, f"sentinel-disposition-request:{sha256_bytes(canonical_json_bytes(seed))}")
        request = DispositionRequest(
            request_id=request_id,
            action=action,
            evidence_ids=tuple(sorted(set(evidence_ids), key=str)),
            subject_digest=subject_digest,
            subject_basis=subject_basis,
            actor=actor,
            reason=reason,
            deadline=deadline,
            created_at=created_at,
            status=DispositionRequestStatus.RESTRICTED,
            legal_exception_reason=legal_exception_reason,
            legal_exception_expires_at=legal_exception_expires_at,
        )
        with self._lock, self._connection:
            row = self._connection.execute("SELECT payload_json FROM disposition_requests WHERE request_id=?", (str(request_id),)).fetchone()
            if row is not None:
                return DispositionRequest.model_validate(json.loads(row[0]))
            self._connection.execute(
                """INSERT INTO disposition_requests(request_id,action,subject_digest,status,deadline,created_at,payload_json)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    str(request_id), action.value, subject_digest, request.status.value, deadline.isoformat(),
                    created_at.isoformat(), request.model_dump_json(),
                ),
            )
            for evidence_id in request.evidence_ids:
                self._connection.execute(
                    "INSERT INTO disposition_request_evidence(request_id,evidence_id) VALUES (?,?)",
                    (str(request_id), str(evidence_id)),
                )
                self._connection.execute(
                    """INSERT INTO disposition_restrictions(evidence_id,request_id,action,created_at)
                       VALUES (?,?,?,?) ON CONFLICT(evidence_id) DO UPDATE SET
                       request_id=excluded.request_id,action=excluded.action,created_at=excluded.created_at""",
                    (str(evidence_id), str(request_id), action.value, created_at.isoformat()),
                )
            if action is DispositionAction.CONSENT_WITHDRAWAL:
                self._connection.execute(
                    """INSERT INTO consent_blocks(subject_digest,request_id,created_at,alternate_basis)
                       VALUES (?,?,?,NULL) ON CONFLICT(subject_digest) DO UPDATE SET
                       request_id=excluded.request_id,created_at=excluded.created_at,alternate_basis=NULL""",
                    (subject_digest, str(request_id), created_at.isoformat()),
                )
            self._authority(str(request_id), created_at, request.model_dump(mode="json"))
        return request

    def request(self, request_id: UUID | str) -> DispositionRequest:
        row = self._connection.execute("SELECT payload_json FROM disposition_requests WHERE request_id=?", (str(request_id),)).fetchone()
        if row is None:
            raise KeyError(str(request_id))
        return DispositionRequest.model_validate(json.loads(row[0]))

    def requests(self) -> tuple[DispositionRequest, ...]:
        rows = self._connection.execute("SELECT payload_json FROM disposition_requests ORDER BY created_at,request_id").fetchall()
        return tuple(DispositionRequest.model_validate(json.loads(row[0])) for row in rows)

    def is_restricted(self, evidence_id: UUID | str) -> bool:
        return self._connection.execute(
            "SELECT 1 FROM disposition_restrictions WHERE evidence_id=?", (str(evidence_id),)
        ).fetchone() is not None

    def processing_allowed(self, *, subject_ref: str, basis: str) -> dict[str, Any]:
        subject_digest = self.subject_digest(subject_ref)
        row = self._connection.execute(
            "SELECT request_id,alternate_basis FROM consent_blocks WHERE subject_digest=?", (subject_digest,)
        ).fetchone()
        if row is None or basis != "consent":
            return {"allowed": True, "subject_digest": subject_digest, "reason_codes": ()}
        if row["alternate_basis"]:
            return {
                "allowed": True,
                "subject_digest": subject_digest,
                "reason_codes": ("consent_withdrawn_alternate_basis_documented",),
                "alternate_basis": row["alternate_basis"],
            }
        return {
            "allowed": False,
            "subject_digest": subject_digest,
            "request_id": row["request_id"],
            "reason_codes": ("consent_withdrawn_future_processing_blocked",),
        }

    def document_alternate_basis(self, subject_ref: str, *, basis: str, actor: str, reason: str) -> None:
        if not basis.strip() or not actor.strip() or not reason.strip():
            raise ValueError("alternate basis governance fields are required")
        digest = self.subject_digest(subject_ref)
        with self._lock, self._connection:
            row = self._connection.execute("SELECT request_id FROM consent_blocks WHERE subject_digest=?", (digest,)).fetchone()
            if row is None:
                raise KeyError(digest)
            self._connection.execute("UPDATE consent_blocks SET alternate_basis=? WHERE subject_digest=?", (basis, digest))
            self._authority(row["request_id"], datetime.now(timezone.utc), {
                "action": "alternate_basis_documented",
                "subject_digest": digest,
                "basis": basis,
                "actor": actor,
                "reason": reason,
            })

    def _record_node_result(self, request_id: UUID, result: DispositionNodeResult) -> DispositionNodeResult:
        payload = result.model_dump(mode="json")
        event_id = uuid5(
            NAMESPACE_URL,
            f"sentinel-disposition-node-event:{request_id}:{result.node_id}:{result.status.value}:{result.receipt_sha256 or ''}",
        )
        with self._connection:
            self._connection.execute(
                """INSERT OR REPLACE INTO disposition_node_events(
                   event_id,request_id,node_id,status,created_at,payload_json) VALUES (?,?,?,?,?,?)""",
                (str(event_id), str(request_id), str(result.node_id), result.status.value, result.updated_at.isoformat(), json.dumps(payload, sort_keys=True)),
            )
        return result

    def acknowledge_external_recipient(
        self,
        node_id: UUID,
        *,
        actor: str,
        receipt: str,
        created_at: datetime | None = None,
    ) -> dict[str, Any]:
        created_at = created_at or datetime.now(timezone.utc)
        row = self._connection.execute(
            "SELECT payload_json FROM disposition_lineage_nodes WHERE node_id=?", (str(node_id),)
        ).fetchone()
        if row is None:
            raise KeyError(str(node_id))
        node = DispositionLineageNode.model_validate(json.loads(row[0]))
        if node.kind not in {DispositionNodeKind.EXTERNAL_RECIPIENT, DispositionNodeKind.EXPORT, DispositionNodeKind.REPLICA}:
            raise ValueError("node is not an external recipient/export/replica")
        receipt_sha256 = sha256_bytes(canonical_json_bytes({
            "node_id": str(node_id), "recipient_digest": node.external_recipient_digest,
            "actor": actor, "receipt": receipt, "created_at": created_at.isoformat(),
        }))
        receipt_id = uuid5(NAMESPACE_URL, f"sentinel-external-receipt:{receipt_sha256}")
        payload = {
            "receipt_id": str(receipt_id),
            "node_id": str(node_id),
            "recipient_digest": node.external_recipient_digest,
            "action": "deletion_acknowledged",
            "actor": actor,
            "created_at": created_at.isoformat(),
            "receipt_sha256": receipt_sha256,
        }
        with self._lock, self._connection:
            self._connection.execute(
                """INSERT OR IGNORE INTO external_recipient_receipts(
                   receipt_id,node_id,recipient_digest,action,actor,created_at,receipt_sha256,payload_json
                   ) VALUES (?,?,?,?,?,?,?,?)""",
                (
                    str(receipt_id), str(node_id), node.external_recipient_digest, "deletion_acknowledged", actor,
                    created_at.isoformat(), receipt_sha256, json.dumps(payload, sort_keys=True),
                ),
            )
            self._authority(str(receipt_id), created_at, payload)
        return payload

    def _external_ack(self, node_id: UUID) -> str | None:
        row = self._connection.execute(
            "SELECT receipt_sha256 FROM external_recipient_receipts WHERE node_id=? ORDER BY created_at DESC LIMIT 1",
            (str(node_id),),
        ).fetchone()
        return str(row[0]) if row else None

    def external_reconciliation_attempts(
        self, request_id: UUID | None = None
    ) -> tuple[ExternalRecipientReconciliationAttempt, ...]:
        if request_id is None:
            rows = self._connection.execute(
                "SELECT payload_json FROM external_recipient_reconciliation_attempts ORDER BY created_at,attempt_id"
            ).fetchall()
        else:
            rows = self._connection.execute(
                "SELECT payload_json FROM external_recipient_reconciliation_attempts WHERE request_id=? ORDER BY created_at,attempt_id",
                (str(request_id),),
            ).fetchall()
        return tuple(ExternalRecipientReconciliationAttempt.model_validate(json.loads(row[0])) for row in rows)

    def reconcile_external_recipients(
        self,
        request_id: UUID,
        *,
        sender: Callable[[DispositionLineageNode], tuple[bool, str]],
        actor: str,
        now: datetime | None = None,
        max_attempts: int = 3,
        retry_delay_seconds: int = 300,
    ) -> ExternalRecipientReconciliationReport:
        if max_attempts <= 0 or retry_delay_seconds <= 0:
            raise ValueError("reconciliation attempt and retry limits must be positive")
        if not actor.strip():
            raise ValueError("reconciliation actor is required")
        now = now or datetime.now(timezone.utc)
        request = self.request(request_id)
        scoped = set(request.evidence_ids)
        nodes = tuple(
            node for evidence_id in scoped for node in self.nodes(evidence_id)
            if node.kind in {DispositionNodeKind.EXTERNAL_RECIPIENT, DispositionNodeKind.EXPORT, DispositionNodeKind.REPLICA}
        )
        attempts: list[ExternalRecipientReconciliationAttempt] = []
        for node in sorted(nodes, key=lambda item: str(item.node_id)):
            recipient_digest = node.external_recipient_digest
            if not recipient_digest:
                raise ValueError("external reconciliation requires a recipient digest")
            acknowledged = self._external_ack(node.node_id)
            previous = [item for item in self.external_reconciliation_attempts(request_id) if item.node_id == node.node_id]
            attempt_no = len(previous) + 1
            response_code: str | None = None
            next_retry: datetime | None = None
            receipt_sha: str | None = acknowledged
            projected_only = False
            if acknowledged:
                state = RecipientReconciliationState.ALREADY_ACKNOWLEDGED
                projected_only = True
            elif previous and previous[-1].state in {
                RecipientReconciliationState.EXHAUSTED,
                RecipientReconciliationState.DEADLINE_EXPIRED,
            }:
                state = previous[-1].state
                attempt_no = previous[-1].attempt_no
                response_code = previous[-1].response_code
                projected_only = True
            elif now >= request.deadline:
                state = RecipientReconciliationState.DEADLINE_EXPIRED
            elif previous and previous[-1].next_retry_at is not None and previous[-1].next_retry_at > now:
                state = RecipientReconciliationState.NOT_DUE
                attempt_no = previous[-1].attempt_no
                next_retry = previous[-1].next_retry_at
                projected_only = True
            else:
                try:
                    success, response_code = sender(node)
                except Exception as exc:  # transport failures become bounded evidence, not worker crashes
                    success = False
                    response_code = f"sender_exception:{type(exc).__name__}"
                if success:
                    receipt = self.acknowledge_external_recipient(
                        node.node_id,
                        actor=actor,
                        receipt=response_code or "recipient_acknowledged",
                        created_at=now,
                    )
                    receipt_sha = str(receipt["receipt_sha256"])
                    state = RecipientReconciliationState.ACKNOWLEDGED
                elif attempt_no >= max_attempts:
                    state = RecipientReconciliationState.EXHAUSTED
                else:
                    state = RecipientReconciliationState.RETRY_SCHEDULED
                    next_retry = now + timedelta(seconds=retry_delay_seconds)
            base = {
                "request_id": str(request_id),
                "node_id": str(node.node_id),
                "recipient_digest": recipient_digest,
                "attempt_no": attempt_no,
                "state": state.value,
                "actor": actor,
                "created_at": now.isoformat(),
                "next_retry_at": next_retry.isoformat() if next_retry else None,
                "response_code": response_code,
                "receipt_sha256": receipt_sha,
            }
            digest = sha256_bytes(canonical_json_bytes(base))
            attempt = ExternalRecipientReconciliationAttempt(
                attempt_id=uuid5(NAMESPACE_URL, f"sentinel-recipient-reconciliation:{digest}"),
                payload_sha256=digest,
                **base,
            )
            # Projection-only states do not create a new immutable transport attempt.
            if not projected_only:
                with self._lock, self._connection:
                    self._connection.execute(
                        """INSERT OR IGNORE INTO external_recipient_reconciliation_attempts(
                           attempt_id,request_id,node_id,recipient_digest,attempt_no,state,created_at,next_retry_at,
                           response_code,receipt_sha256,payload_sha256,payload_json
                           ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            str(attempt.attempt_id), str(request_id), str(node.node_id), recipient_digest,
                            attempt.attempt_no, attempt.state.value, attempt.created_at.isoformat(),
                            attempt.next_retry_at.isoformat() if attempt.next_retry_at else None,
                            attempt.response_code, attempt.receipt_sha256, attempt.payload_sha256,
                            attempt.model_dump_json(),
                        ),
                    )
                    self._authority(str(attempt.attempt_id), now, attempt.model_dump(mode="json"))
            attempts.append(attempt)
        acknowledged_count = sum(item.state in {RecipientReconciliationState.ACKNOWLEDGED, RecipientReconciliationState.ALREADY_ACKNOWLEDGED} for item in attempts)
        retry_count = sum(item.state in {RecipientReconciliationState.RETRY_SCHEDULED, RecipientReconciliationState.NOT_DUE} for item in attempts)
        exhausted_count = sum(item.state is RecipientReconciliationState.EXHAUSTED for item in attempts)
        expired_count = sum(item.state is RecipientReconciliationState.DEADLINE_EXPIRED for item in attempts)
        pending = retry_count + exhausted_count + expired_count
        report_base = {
            "request_id": str(request_id),
            "generated_at": now.isoformat(),
            "attempts": [item.model_dump(mode="json") for item in attempts],
            "acknowledged": acknowledged_count,
            "retry_scheduled": retry_count,
            "exhausted": exhausted_count,
            "deadline_expired": expired_count,
            "pending": pending,
            "complete": pending == 0,
        }
        report = ExternalRecipientReconciliationReport(
            **report_base,
            report_sha256=sha256_bytes(canonical_json_bytes(report_base)),
        )
        self._authority(str(request_id), now, {"external_recipient_reconciliation": report.model_dump(mode="json")})
        return report

    def close(self, request_id: UUID, *, evidence_service: Any, artifact_store: Any, now: datetime | None = None) -> DispositionReport:
        now = now or datetime.now(timezone.utc)
        request = self.request(request_id)
        with self._connection:
            in_progress = request.model_copy(update={"status": DispositionRequestStatus.IN_PROGRESS})
            self._connection.execute(
                "UPDATE disposition_requests SET status=?,payload_json=? WHERE request_id=?",
                (in_progress.status.value, in_progress.model_dump_json(), str(request_id)),
            )
        results: list[DispositionNodeResult] = []
        for evidence_id in request.evidence_ids:
            nodes = self.nodes(evidence_id)
            for node in nodes:
                status = DispositionNodeStatus.RESTRICTED
                reasons: list[str] = []
                receipt_sha256 = None
                if node.exception_reason and (node.exception_expires_at is None or node.exception_expires_at > now):
                    status = DispositionNodeStatus.RETAINED_EXCEPTION
                    reasons.append("explicit_retained_exception")
                elif node.kind in {DispositionNodeKind.EXTERNAL_RECIPIENT, DispositionNodeKind.EXPORT, DispositionNodeKind.REPLICA}:
                    receipt_sha256 = self._external_ack(node.node_id)
                    if receipt_sha256:
                        status = DispositionNodeStatus.DELETED
                        reasons.append("external_deletion_acknowledged")
                    else:
                        status = DispositionNodeStatus.EXTERNAL_PENDING
                        reasons.append("external_recipient_pending")
                elif node.kind in {DispositionNodeKind.GRANT, DispositionNodeKind.LEASE}:
                    if node.target_ref.startswith("artifact-reference:"):
                        try:
                            artifact_store.catalog.remove_reference(node.target_ref.split(":", 1)[1])
                            status = DispositionNodeStatus.REVOKED
                            reasons.append("artifact_reference_revoked")
                        except Exception as exc:  # explicit failure evidence, not silent best effort
                            status = DispositionNodeStatus.FAILED
                            reasons.append(f"reference_revocation_failed:{type(exc).__name__}")
                    else:
                        status = DispositionNodeStatus.REVOKED
                        reasons.append("logical_grant_revoked")
                elif node.target_ref.startswith("artifact-sha256:"):
                    digest = node.target_ref.split(":", 1)[1]
                    try:
                        receipt = artifact_store.delete_digest(
                            digest, actor=request.actor, tombstone_authorized=True,
                        )
                        status = DispositionNodeStatus.DELETED
                        receipt_sha256 = str(receipt["deletion_proof_sha256"])
                        reasons.append("local_artifact_deleted")
                    except PermissionError as exc:
                        status = DispositionNodeStatus.RETAINED_EXCEPTION
                        reasons.append(f"artifact_retained:{exc}")
                    except Exception as exc:
                        status = DispositionNodeStatus.FAILED
                        reasons.append(f"artifact_deletion_failed:{type(exc).__name__}")
                else:
                    status = DispositionNodeStatus.DELETED
                    reasons.append("logical_descendant_removed")
                result = DispositionNodeResult(
                    node_id=node.node_id,
                    evidence_id=node.evidence_id,
                    kind=node.kind,
                    status=status,
                    target_digest=sha256_bytes(node.target_ref.encode("utf-8")),
                    reason_codes=tuple(reasons),
                    updated_at=now,
                    receipt_sha256=receipt_sha256,
                )
                self._record_node_result(request_id, result)
                results.append(result)

            if request.action is DispositionAction.ERASE:
                try:
                    projection = evidence_service.lifecycle(evidence_id)
                    if projection.state is not EvidenceContentState.DELETED:
                        evidence_service.transition(
                            evidence_id,
                            to_state=EvidenceContentState.DELETED,
                            expected_version=projection.version,
                            actor=request.actor,
                            reason=request.reason,
                            now=now,
                        )
                except Exception as exc:
                    synthetic_id = uuid5(NAMESPACE_URL, f"sentinel-disposition-evidence-failure:{request_id}:{evidence_id}")
                    results.append(self._record_node_result(request_id, DispositionNodeResult(
                        node_id=synthetic_id,
                        evidence_id=evidence_id,
                        kind=DispositionNodeKind.ORIGINAL,
                        status=DispositionNodeStatus.FAILED,
                        target_digest=sha256_bytes(f"evidence:{evidence_id}".encode()),
                        reason_codes=(f"evidence_lifecycle_delete_failed:{type(exc).__name__}",),
                        updated_at=now,
                    )))

        completed = sum(item.status in {DispositionNodeStatus.DELETED, DispositionNodeStatus.REVOKED} for item in results)
        retained = sum(item.status is DispositionNodeStatus.RETAINED_EXCEPTION for item in results)
        external = sum(item.status is DispositionNodeStatus.EXTERNAL_PENDING for item in results)
        failed = sum(item.status is DispositionNodeStatus.FAILED for item in results)
        restricted = sum(item.status is DispositionNodeStatus.RESTRICTED for item in results)
        if failed:
            status = DispositionRequestStatus.FAILED
            terminal = "closure_failed"
        elif external:
            status = DispositionRequestStatus.EXTERNAL_RECIPIENT_PENDING
            terminal = "external_recipients_unresolved"
        elif retained:
            status = DispositionRequestStatus.RETAINED_EXCEPTION
            terminal = "retained_by_explicit_exception"
        else:
            status = DispositionRequestStatus.COMPLETED
            terminal = "closure_complete"
            with self._connection:
                for evidence_id in request.evidence_ids:
                    self._connection.execute("DELETE FROM disposition_restrictions WHERE evidence_id=?", (str(evidence_id),))
        report_base = {
            "request_id": str(request_id),
            "status": status.value,
            "completed": completed,
            "retained_by_exception": retained,
            "external_recipient_pending": external,
            "failed": failed,
            "restricted": restricted,
            "node_results": [item.model_dump(mode="json") for item in results],
            "subject_digest": request.subject_digest,
            "deadline": request.deadline.isoformat(),
            "terminal_outcome": terminal,
            "generated_at": now.isoformat(),
        }
        report = DispositionReport.model_validate({
            **report_base,
            "report_sha256": sha256_bytes(canonical_json_bytes(report_base)),
        })
        updated = request.model_copy(update={"status": status, "terminal_outcome": terminal})
        with self._lock, self._connection:
            self._connection.execute(
                "UPDATE disposition_requests SET status=?,payload_json=? WHERE request_id=?",
                (status.value, updated.model_dump_json(), str(request_id)),
            )
            self._authority(str(request_id), now, report.model_dump(mode="json"))
        return report

    def latest_results(self, request_id: UUID) -> tuple[DispositionNodeResult, ...]:
        rows = self._connection.execute(
            """SELECT payload_json FROM disposition_node_events WHERE request_id=?
               ORDER BY created_at,event_id""", (str(request_id),)
        ).fetchall()
        latest: dict[str, DispositionNodeResult] = {}
        for row in rows:
            item = DispositionNodeResult.model_validate(json.loads(row[0]))
            latest[str(item.node_id)] = item
        return tuple(sorted(latest.values(), key=lambda item: str(item.node_id)))

    def minimal_tombstone(self, request_id: UUID) -> dict[str, Any]:
        request = self.request(request_id)
        results = self.latest_results(request_id)
        payload = {
            "schema": "sentinel-edge-disposition-tombstone/1.0",
            "request_id": str(request.request_id),
            "action": request.action.value,
            "subject_digest": request.subject_digest,
            "evidence_count": len(request.evidence_ids),
            "terminal_outcome": request.terminal_outcome,
            "result_counts": {
                state.value: sum(item.status is state for item in results) for state in DispositionNodeStatus
            },
            "content_retained": False,
            "exact_location_retained": False,
            "recipient_identities_retained": False,
        }
        return {**payload, "tombstone_sha256": sha256_bytes(canonical_json_bytes(payload))}

    def close_store(self) -> None:
        self._connection.close()
