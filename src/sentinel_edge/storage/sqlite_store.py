from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from uuid import NAMESPACE_URL, uuid5

from sentinel_edge.security import canonical_json_bytes, sha256_bytes

from sentinel_edge.domain.models import (
    AuthorityMutation,
    AuthorityMutationKind,
    ConfigurationActivationRecord,
    ConfigurationBundle,
    ConfigurationState,
    CommandReceipt,
    CommandStatus,
    EvidenceItem,
    EvidenceContentState,
    EvidenceLifecycleAction,
    EvidenceLifecycleEvent,
    EvidenceLifecycleProjection,
    MediaParserReport,
    EvidenceReevaluationRecord,
    ClaimNode,
    ClaimEvidenceLink,
    IncidentRelation,
    IncidentCandidate,
    IncidentIdentityDecision,
    IncidentRecord,
    IncidentReviewState,
    NotificationIntent,
    NotificationStatus,
    ReviewAction,
    ReviewActionKind,
    SourceHealth,
    SourceHealthEvent,
)


class IncidentJournalStore:
    """Component-4-owned WAL journal, review state, and transactional notification outbox."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=FULL")
        self._connection.execute("PRAGMA busy_timeout=5000")
        self._connection.row_factory = sqlite3.Row
        self._lock = RLock()
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS authority_events (
                position INTEGER PRIMARY KEY AUTOINCREMENT,
                epoch_id TEXT NOT NULL DEFAULT 'authority-epoch-1',
                epoch_ordinal INTEGER,
                predecessor_position INTEGER,
                kind TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                accepted_at TEXT NOT NULL,
                payload_sha256 TEXT,
                payload_json TEXT NOT NULL,
                UNIQUE(epoch_id, epoch_ordinal)
            );
            CREATE TABLE IF NOT EXISTS authority_event_subtypes (
                authority_position INTEGER PRIMARY KEY,
                kind TEXT NOT NULL,
                subtype_id TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                FOREIGN KEY(authority_position) REFERENCES authority_events(position)
            );
            CREATE TABLE IF NOT EXISTS incident_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                authority_position INTEGER UNIQUE,
                incident_id TEXT NOT NULL,
                hazard TEXT NOT NULL,
                version INTEGER NOT NULL,
                state TEXT NOT NULL,
                accepted_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                UNIQUE(incident_id, version),
                FOREIGN KEY(authority_position) REFERENCES authority_events(position)
            );
            CREATE INDEX IF NOT EXISTS idx_incident_events_hazard_version
                ON incident_events(hazard, version DESC);
            CREATE TABLE IF NOT EXISTS notification_intents (
                notification_id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                hazard TEXT NOT NULL,
                incident_version INTEGER NOT NULL,
                incident_state TEXT NOT NULL,
                idempotency_key TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                attempt_count INTEGER NOT NULL,
                max_attempts INTEGER NOT NULL,
                last_error TEXT,
                receipt_id TEXT,
                reason_codes_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_notification_status_created
                ON notification_intents(status, created_at);
            CREATE TABLE IF NOT EXISTS review_actions (
                review_id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                hazard TEXT NOT NULL,
                action TEXT NOT NULL,
                actor TEXT NOT NULL,
                created_at TEXT NOT NULL,
                snooze_until TEXT,
                comment TEXT,
                payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS incident_review_state (
                incident_id TEXT PRIMARY KEY,
                acknowledged_at TEXT,
                acknowledged_by TEXT,
                snoozed_until TEXT,
                snoozed_by TEXT,
                review_count INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS command_receipts (
                command_id TEXT PRIMARY KEY,
                principal_id TEXT NOT NULL,
                operation TEXT NOT NULL,
                target TEXT NOT NULL,
                scoped_idempotency_key TEXT NOT NULL UNIQUE,
                payload_sha256 TEXT NOT NULL,
                status TEXT NOT NULL,
                accepted_at TEXT NOT NULL,
                committed_at TEXT,
                result_version INTEGER,
                result_sha256 TEXT,
                reason_codes_json TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_command_receipts_principal_operation
                ON command_receipts(principal_id, operation, target);
            CREATE TABLE IF NOT EXISTS evidence_items (
                evidence_id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                hazard TEXT NOT NULL,
                family_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                content_sha256 TEXT NOT NULL,
                perceptual_hash TEXT,
                origin_key TEXT NOT NULL,
                independent_origin_proven INTEGER NOT NULL,
                received_at TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_evidence_incident_family
                ON evidence_items(incident_id, family_id, received_at);
            CREATE INDEX IF NOT EXISTS idx_evidence_content
                ON evidence_items(content_sha256, perceptual_hash);
            CREATE TABLE IF NOT EXISTS evidence_lifecycle_events (
                lifecycle_event_id TEXT PRIMARY KEY,
                evidence_id TEXT NOT NULL,
                incident_id TEXT NOT NULL,
                action TEXT NOT NULL,
                from_state TEXT,
                to_state TEXT NOT NULL,
                expected_version INTEGER NOT NULL,
                resulting_version INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                UNIQUE(evidence_id, resulting_version),
                FOREIGN KEY(evidence_id) REFERENCES evidence_items(evidence_id)
            );
            CREATE INDEX IF NOT EXISTS idx_evidence_lifecycle_evidence_version
                ON evidence_lifecycle_events(evidence_id, resulting_version);
            CREATE INDEX IF NOT EXISTS idx_evidence_lifecycle_incident_time
                ON evidence_lifecycle_events(incident_id, created_at);
            CREATE TABLE IF NOT EXISTS media_parser_runs (
                parse_id TEXT PRIMARY KEY,
                input_sha256 TEXT NOT NULL,
                output_sha256 TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_media_parser_input
                ON media_parser_runs(input_sha256, created_at);
            CREATE TABLE IF NOT EXISTS evidence_reevaluations (
                reevaluation_id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                evidence_id TEXT NOT NULL,
                trigger_action TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_evidence_reevaluation_incident
                ON evidence_reevaluations(incident_id, created_at);
            CREATE TABLE IF NOT EXISTS claim_nodes (
                claim_id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                hazard TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_claim_incident
                ON claim_nodes(incident_id, created_at);
            CREATE TABLE IF NOT EXISTS claim_evidence_links (
                link_id TEXT PRIMARY KEY,
                claim_id TEXT NOT NULL,
                evidence_id TEXT NOT NULL,
                relation TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                UNIQUE(claim_id, evidence_id, relation),
                FOREIGN KEY(claim_id) REFERENCES claim_nodes(claim_id),
                FOREIGN KEY(evidence_id) REFERENCES evidence_items(evidence_id)
            );
            CREATE TABLE IF NOT EXISTS incident_relations (
                relation_id TEXT PRIMARY KEY,
                source_incident_id TEXT NOT NULL,
                source_hazard TEXT NOT NULL,
                target_incident_id TEXT NOT NULL,
                target_hazard TEXT NOT NULL,
                relation TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                UNIQUE(source_incident_id, target_incident_id, relation)
            );
            CREATE TABLE IF NOT EXISTS incident_candidates (
                candidate_id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                hazard TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                source_id TEXT NOT NULL,
                source_event_id TEXT,
                payload_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_incident_candidates_hazard_time
                ON incident_candidates(hazard, observed_at);
            CREATE INDEX IF NOT EXISTS idx_incident_candidates_source_event
                ON incident_candidates(source_id, source_event_id) WHERE source_event_id IS NOT NULL;
            CREATE TABLE IF NOT EXISTS incident_identity_decisions (
                decision_id TEXT PRIMARY KEY,
                candidate_id TEXT NOT NULL UNIQUE,
                incident_id TEXT NOT NULL,
                outcome TEXT NOT NULL,
                decided_at TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                FOREIGN KEY(candidate_id) REFERENCES incident_candidates(candidate_id)
            );
            """
        )
        self._migrate_authority_schema()
        self._migrate_legacy_incident_journal()
        self._backfill_authority_subtypes()

    def close(self) -> None:
        self._connection.close()

    def _migrate_authority_schema(self) -> None:
        columns = {row[1] for row in self._connection.execute("PRAGMA table_info(authority_events)").fetchall()}
        additions = {
            "epoch_id": "TEXT NOT NULL DEFAULT 'authority-epoch-1'",
            "epoch_ordinal": "INTEGER",
            "predecessor_position": "INTEGER",
            "payload_sha256": "TEXT",
        }
        for name, declaration in additions.items():
            if name not in columns:
                self._connection.execute(f"ALTER TABLE authority_events ADD COLUMN {name} {declaration}")
        self._connection.execute(
            """CREATE TABLE IF NOT EXISTS authority_event_subtypes (
                authority_position INTEGER PRIMARY KEY,
                kind TEXT NOT NULL,
                subtype_id TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                FOREIGN KEY(authority_position) REFERENCES authority_events(position)
            )"""
        )
        previous: int | None = None
        rows = self._connection.execute(
            "SELECT position,payload_json FROM authority_events ORDER BY position"
        ).fetchall()
        with self._connection:
            for ordinal, row in enumerate(rows, start=1):
                payload = json.loads(row["payload_json"])
                digest = sha256_bytes(canonical_json_bytes(payload))
                self._connection.execute(
                    """UPDATE authority_events SET epoch_id='authority-epoch-1',epoch_ordinal=?,
                       predecessor_position=?,payload_sha256=? WHERE position=?""",
                    (ordinal, previous, digest, row["position"]),
                )
                previous = int(row["position"])

    def _backfill_authority_subtypes(self) -> None:
        rows = self._connection.execute(
            """SELECT position,kind,entity_id,payload_sha256,payload_json FROM authority_events
               WHERE position NOT IN (SELECT authority_position FROM authority_event_subtypes)
               ORDER BY position"""
        ).fetchall()
        with self._connection:
            for row in rows:
                digest = row["payload_sha256"] or sha256_bytes(canonical_json_bytes(json.loads(row["payload_json"])))
                self._connection.execute(
                    """INSERT INTO authority_event_subtypes(
                       authority_position,kind,subtype_id,payload_sha256,payload_json
                       ) VALUES (?,?,?,?,?)""",
                    (row["position"], row["kind"], row["entity_id"], digest, row["payload_json"]),
                )

    def _migrate_legacy_incident_journal(self) -> None:
        columns = {row[1] for row in self._connection.execute("PRAGMA table_info(incident_events)").fetchall()}
        if "authority_position" not in columns:
            self._connection.execute("ALTER TABLE incident_events ADD COLUMN authority_position INTEGER")
        rows = self._connection.execute(
            "SELECT event_id,incident_id,accepted_at,payload_json FROM incident_events WHERE authority_position IS NULL ORDER BY event_id"
        ).fetchall()
        with self._connection:
            for row in rows:
                payload = json.loads(row["payload_json"])
                position = self._append_authority(
                    AuthorityMutationKind.INCIDENT, row["incident_id"], datetime.fromisoformat(row["accepted_at"]), payload
                )
                self._connection.execute(
                    "UPDATE incident_events SET authority_position=? WHERE event_id=?", (position, row["event_id"])
                )

    def _append_authority(self, kind: AuthorityMutationKind, entity_id: str, accepted_at: datetime, payload: dict) -> int:
        payload_json = json.dumps(payload, sort_keys=True)
        payload_sha256 = sha256_bytes(canonical_json_bytes(payload))
        previous = self._connection.execute(
            "SELECT position,epoch_ordinal FROM authority_events ORDER BY position DESC LIMIT 1"
        ).fetchone()
        predecessor = int(previous["position"]) if previous is not None else None
        ordinal = int(previous["epoch_ordinal"] or previous["position"]) + 1 if previous is not None else 1
        cursor = self._connection.execute(
            """INSERT INTO authority_events(
               epoch_id,epoch_ordinal,predecessor_position,kind,entity_id,accepted_at,payload_sha256,payload_json
               ) VALUES (?,?,?,?,?,?,?,?)""",
            ("authority-epoch-1", ordinal, predecessor, kind.value, entity_id, accepted_at.isoformat(), payload_sha256, payload_json),
        )
        position = int(cursor.lastrowid)
        self._connection.execute(
            """INSERT INTO authority_event_subtypes(
               authority_position,kind,subtype_id,payload_sha256,payload_json
               ) VALUES (?,?,?,?,?)""",
            (position, kind.value, entity_id, payload_sha256, payload_json),
        )
        return position

    def record_authority_mutation(
        self,
        kind: str | AuthorityMutationKind,
        entity_id: str,
        accepted_at: datetime,
        payload: dict,
    ) -> int:
        resolved = kind if isinstance(kind, AuthorityMutationKind) else AuthorityMutationKind(kind)
        with self._lock, self._connection:
            return self._append_authority(resolved, entity_id, accepted_at, payload)

    def append(self, incident: IncidentRecord) -> None:
        self.append_incident_with_notification(incident, None)

    def append_incident_with_notification(
        self, incident: IncidentRecord, notification: NotificationIntent | None
    ) -> bool:
        """Commit event truth and any accepted notification intent in one transaction."""
        with self._lock, self._connection:
            position = self._append_authority(
                AuthorityMutationKind.INCIDENT,
                str(incident.incident_id),
                incident.last_observed_at,
                incident.model_dump(mode="json"),
            )
            self._connection.execute(
                """
                INSERT INTO incident_events(
                    authority_position,incident_id,hazard,version,state,accepted_at,payload_json
                ) VALUES (?,?,?,?,?,?,?)
                """,
                (
                    position,
                    str(incident.incident_id),
                    incident.hazard.value,
                    incident.version,
                    incident.state.value,
                    incident.last_observed_at.isoformat(),
                    incident.model_dump_json(),
                ),
            )
            inserted = False
            if notification is not None:
                exists = self._connection.execute(
                    "SELECT 1 FROM notification_intents WHERE idempotency_key=?",
                    (notification.idempotency_key,),
                ).fetchone()
                if exists is None:
                    self._append_authority(
                        AuthorityMutationKind.NOTIFICATION_INTENT,
                        str(notification.notification_id),
                        notification.created_at,
                        notification.model_dump(mode="json"),
                    )
                    self._insert_notification(notification)
                    inserted = True
            return inserted

    def _insert_notification(self, item: NotificationIntent) -> None:
        self._connection.execute(
            """
            INSERT INTO notification_intents(
                notification_id,incident_id,hazard,incident_version,incident_state,idempotency_key,
                status,created_at,updated_at,attempt_count,max_attempts,last_error,receipt_id,reason_codes_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                str(item.notification_id),
                str(item.incident_id),
                item.hazard.value,
                item.incident_version,
                item.incident_state.value,
                item.idempotency_key,
                item.status.value,
                item.created_at.isoformat(),
                item.updated_at.isoformat(),
                item.attempt_count,
                item.max_attempts,
                item.last_error,
                item.receipt_id,
                json.dumps(list(item.reason_codes), sort_keys=True),
            ),
        )

    @staticmethod
    def _notification_from_row(row: sqlite3.Row) -> NotificationIntent:
        return NotificationIntent(
            notification_id=row["notification_id"],
            incident_id=row["incident_id"],
            hazard=row["hazard"],
            incident_version=row["incident_version"],
            incident_state=row["incident_state"],
            idempotency_key=row["idempotency_key"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            attempt_count=row["attempt_count"],
            max_attempts=row["max_attempts"],
            last_error=row["last_error"],
            receipt_id=row["receipt_id"],
            reason_codes=tuple(json.loads(row["reason_codes_json"])),
        )

    def all(self) -> tuple[IncidentRecord, ...]:
        rows = self._connection.execute(
            "SELECT payload_json FROM incident_events ORDER BY event_id"
        ).fetchall()
        return tuple(IncidentRecord.model_validate(json.loads(row[0])) for row in rows)

    def latest_by_hazard(self) -> tuple[IncidentRecord, ...]:
        rows = self._connection.execute(
            """
            SELECT payload_json FROM incident_events e
            WHERE version = (
                SELECT MAX(e2.version) FROM incident_events e2 WHERE e2.hazard = e.hazard
            )
            ORDER BY hazard
            """
        ).fetchall()
        return tuple(IncidentRecord.model_validate(json.loads(row[0])) for row in rows)

    def authority_journal(self) -> tuple[AuthorityMutation, ...]:
        rows = self._connection.execute(
            "SELECT position,kind,entity_id,accepted_at,payload_json FROM authority_events ORDER BY position"
        ).fetchall()
        return tuple(
            AuthorityMutation(
                position=row["position"],
                kind=row["kind"],
                entity_id=row["entity_id"],
                accepted_at=datetime.fromisoformat(row["accepted_at"]),
                payload=json.loads(row["payload_json"]),
            )
            for row in rows
        )

    def notifications(self) -> tuple[NotificationIntent, ...]:
        rows = self._connection.execute(
            "SELECT * FROM notification_intents ORDER BY created_at,notification_id"
        ).fetchall()
        return tuple(self._notification_from_row(row) for row in rows)

    def dispatchable_notifications(self, now: datetime | None = None) -> tuple[NotificationIntent, ...]:
        now = now or datetime.now(timezone.utc)
        rows = self._connection.execute(
            """
            SELECT * FROM notification_intents
            WHERE status IN (?,?) AND attempt_count < max_attempts
            ORDER BY created_at,notification_id
            """,
            (NotificationStatus.PENDING.value, NotificationStatus.FAILED.value),
        ).fetchall()
        return tuple(item for item in (self._notification_from_row(row) for row in rows) if item.created_at <= now)

    def record_delivery(
        self,
        notification_id: str,
        *,
        delivered: bool,
        receipt_id: str | None = None,
        error: str | None = None,
        accepted_at: datetime | None = None,
    ) -> NotificationIntent:
        accepted_at = accepted_at or datetime.now(timezone.utc)
        with self._lock, self._connection:
            row = self._connection.execute(
                "SELECT * FROM notification_intents WHERE notification_id=?", (notification_id,)
            ).fetchone()
            if row is None:
                raise KeyError(notification_id)
            current = self._notification_from_row(row)
            if current.status is NotificationStatus.DELIVERED:
                return current
            attempts = current.attempt_count + 1
            if delivered:
                status = NotificationStatus.DELIVERED
            elif attempts >= current.max_attempts:
                status = NotificationStatus.DEAD_LETTER
            else:
                status = NotificationStatus.FAILED
            updated = current.model_copy(
                update={
                    "status": status,
                    "attempt_count": attempts,
                    "updated_at": accepted_at,
                    "receipt_id": receipt_id if delivered else None,
                    "last_error": None if delivered else (error or "delivery_failed"),
                }
            )
            self._append_authority(
                AuthorityMutationKind.NOTIFICATION_DELIVERY,
                str(updated.notification_id),
                accepted_at,
                updated.model_dump(mode="json"),
            )
            self._connection.execute(
                """
                UPDATE notification_intents SET status=?,updated_at=?,attempt_count=?,last_error=?,receipt_id=?
                WHERE notification_id=?
                """,
                (
                    updated.status.value,
                    updated.updated_at.isoformat(),
                    updated.attempt_count,
                    updated.last_error,
                    updated.receipt_id,
                    str(updated.notification_id),
                ),
            )
            return updated

    def notification_count(self, incident_id: str) -> int:
        row = self._connection.execute(
            "SELECT COUNT(*) FROM notification_intents WHERE incident_id=?", (incident_id,)
        ).fetchone()
        return int(row[0])

    def notification_metrics(self, now: datetime | None = None) -> dict[str, int | float]:
        now = now or datetime.now(timezone.utc)
        items = self.notifications()
        pending = [item for item in items if item.status in {NotificationStatus.PENDING, NotificationStatus.FAILED}]
        backlog_age = max(((now - item.created_at).total_seconds() for item in pending), default=0.0)
        counts = {status.value: sum(item.status is status for item in items) for status in NotificationStatus}
        counts["total"] = len(items)
        counts["backlog_age_seconds"] = max(0.0, backlog_age)
        return counts

    def record_review(self, action: ReviewAction) -> IncidentReviewState:
        with self._lock, self._connection:
            current = self.review_state(str(action.incident_id))
            if action.action is ReviewActionKind.ACKNOWLEDGE:
                updated = current.model_copy(
                    update={
                        "acknowledged_at": action.created_at,
                        "acknowledged_by": action.actor,
                        "review_count": current.review_count + 1,
                    }
                )
            elif action.action is ReviewActionKind.SNOOZE:
                updated = current.model_copy(
                    update={
                        "snoozed_until": action.snooze_until,
                        "snoozed_by": action.actor,
                        "review_count": current.review_count + 1,
                    }
                )
            elif action.action is ReviewActionKind.UNSNOOZE:
                updated = current.model_copy(
                    update={"snoozed_until": None, "snoozed_by": None, "review_count": current.review_count + 1}
                )
            else:
                updated = current.model_copy(update={"review_count": current.review_count + 1})
            self._append_authority(
                AuthorityMutationKind.REVIEW,
                str(action.review_id),
                action.created_at,
                action.model_dump(mode="json"),
            )
            self._connection.execute(
                """
                INSERT INTO review_actions(review_id,incident_id,hazard,action,actor,created_at,snooze_until,comment,payload_json)
                VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (
                    str(action.review_id),
                    str(action.incident_id),
                    action.hazard.value,
                    action.action.value,
                    action.actor,
                    action.created_at.isoformat(),
                    action.snooze_until.isoformat() if action.snooze_until else None,
                    action.comment,
                    action.model_dump_json(),
                ),
            )
            self._connection.execute(
                """
                INSERT INTO incident_review_state(
                    incident_id,acknowledged_at,acknowledged_by,snoozed_until,snoozed_by,review_count
                ) VALUES (?,?,?,?,?,?)
                ON CONFLICT(incident_id) DO UPDATE SET
                    acknowledged_at=excluded.acknowledged_at,
                    acknowledged_by=excluded.acknowledged_by,
                    snoozed_until=excluded.snoozed_until,
                    snoozed_by=excluded.snoozed_by,
                    review_count=excluded.review_count
                """,
                (
                    str(updated.incident_id),
                    updated.acknowledged_at.isoformat() if updated.acknowledged_at else None,
                    updated.acknowledged_by,
                    updated.snoozed_until.isoformat() if updated.snoozed_until else None,
                    updated.snoozed_by,
                    updated.review_count,
                ),
            )
            return updated

    def review_state(self, incident_id: str) -> IncidentReviewState:
        row = self._connection.execute(
            "SELECT * FROM incident_review_state WHERE incident_id=?", (incident_id,)
        ).fetchone()
        if row is None:
            return IncidentReviewState(incident_id=incident_id)
        return IncidentReviewState(
            incident_id=row["incident_id"],
            acknowledged_at=datetime.fromisoformat(row["acknowledged_at"]) if row["acknowledged_at"] else None,
            acknowledged_by=row["acknowledged_by"],
            snoozed_until=datetime.fromisoformat(row["snoozed_until"]) if row["snoozed_until"] else None,
            snoozed_by=row["snoozed_by"],
            review_count=row["review_count"],
        )

    def reviews(self) -> tuple[ReviewAction, ...]:
        rows = self._connection.execute(
            "SELECT payload_json FROM review_actions ORDER BY created_at,review_id"
        ).fetchall()
        return tuple(ReviewAction.model_validate(json.loads(row[0])) for row in rows)

    def review_states(self) -> tuple[IncidentReviewState, ...]:
        rows = self._connection.execute(
            "SELECT incident_id FROM incident_review_state ORDER BY incident_id"
        ).fetchall()
        return tuple(self.review_state(row[0]) for row in rows)

    def command_receipt(self, scoped_idempotency_key: str) -> CommandReceipt | None:
        row = self._connection.execute(
            "SELECT payload_json FROM command_receipts WHERE scoped_idempotency_key=?",
            (scoped_idempotency_key,),
        ).fetchone()
        return CommandReceipt.model_validate(json.loads(row[0])) if row else None

    def record_command_receipt(self, receipt: CommandReceipt) -> CommandReceipt:
        with self._lock, self._connection:
            existing = self.command_receipt(receipt.scoped_idempotency_key)
            if existing is not None:
                if existing.payload_sha256 != receipt.payload_sha256:
                    raise ValueError("idempotency key reused with a different payload")
                return existing
            self._append_authority(
                AuthorityMutationKind.COMMAND,
                str(receipt.command_id),
                receipt.committed_at or receipt.accepted_at,
                receipt.model_dump(mode="json"),
            )
            self._connection.execute(
                """
                INSERT INTO command_receipts(
                    command_id,principal_id,operation,target,scoped_idempotency_key,payload_sha256,status,
                    accepted_at,committed_at,result_version,result_sha256,reason_codes_json,payload_json
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    str(receipt.command_id),
                    receipt.principal_id,
                    receipt.operation,
                    receipt.target,
                    receipt.scoped_idempotency_key,
                    receipt.payload_sha256,
                    receipt.status.value,
                    receipt.accepted_at.isoformat(),
                    receipt.committed_at.isoformat() if receipt.committed_at else None,
                    receipt.result_version,
                    receipt.result_sha256,
                    json.dumps(list(receipt.reason_codes), sort_keys=True),
                    receipt.model_dump_json(),
                ),
            )
            return receipt

    def command_receipts(self) -> tuple[CommandReceipt, ...]:
        rows = self._connection.execute(
            "SELECT payload_json FROM command_receipts ORDER BY accepted_at,command_id"
        ).fetchall()
        return tuple(CommandReceipt.model_validate(json.loads(row[0])) for row in rows)

    def record_evidence(self, item: EvidenceItem) -> EvidenceItem:
        if item.family_id is None:
            raise ValueError("evidence family_id must be assigned before persistence")
        payload = item.model_dump(mode="json")
        digest = sha256_bytes(canonical_json_bytes(payload))
        with self._lock, self._connection:
            row = self._connection.execute(
                "SELECT payload_sha256,payload_json FROM evidence_items WHERE evidence_id=?",
                (str(item.evidence_id),),
            ).fetchone()
            if row is not None:
                if row["payload_sha256"] != digest:
                    raise ValueError("evidence identity conflict")
                return EvidenceItem.model_validate(json.loads(row["payload_json"]))
            self._append_authority(
                AuthorityMutationKind.EVIDENCE, str(item.evidence_id), item.received_at, payload
            )
            self._connection.execute(
                """INSERT INTO evidence_items(
                   evidence_id,incident_id,hazard,family_id,source_id,content_sha256,perceptual_hash,origin_key,
                   independent_origin_proven,received_at,payload_sha256,payload_json
                   ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    str(item.evidence_id), str(item.incident_id), item.hazard.value, item.family_id, item.source_id,
                    item.content_sha256, item.perceptual_hash, item.origin_key, int(item.independent_origin_proven),
                    item.received_at.isoformat(), digest, item.model_dump_json(),
                ),
            )
            if item.retention_state.value == "retained":
                initial_state = EvidenceContentState.AVAILABLE
            elif item.retention_state.value == "metadata_only":
                initial_state = EvidenceContentState.METADATA_ONLY
            else:
                initial_state = EvidenceContentState.UNAVAILABLE_AT_CAPTURE
            initial = EvidenceLifecycleEvent(
                evidence_id=item.evidence_id,
                incident_id=item.incident_id,
                action=EvidenceLifecycleAction.REGISTER,
                from_state=None,
                to_state=initial_state,
                expected_version=0,
                resulting_version=1,
                actor="component-4-evidence-ingest",
                reason="evidence_registered",
                created_at=item.received_at,
                reason_codes=(f"initial_retention:{item.retention_state.value}",),
            )
            self._record_evidence_lifecycle_locked(initial)
            return item

    def evidence(self, incident_id: str | None = None) -> tuple[EvidenceItem, ...]:
        if incident_id is None:
            rows = self._connection.execute(
                "SELECT payload_json FROM evidence_items ORDER BY received_at,evidence_id"
            ).fetchall()
        else:
            rows = self._connection.execute(
                "SELECT payload_json FROM evidence_items WHERE incident_id=? ORDER BY received_at,evidence_id",
                (incident_id,),
            ).fetchall()
        return tuple(EvidenceItem.model_validate(json.loads(row[0])) for row in rows)

    def _record_evidence_lifecycle_locked(self, event: EvidenceLifecycleEvent) -> EvidenceLifecycleEvent:
        payload = event.model_dump(mode="json")
        digest = sha256_bytes(canonical_json_bytes(payload))
        row = self._connection.execute(
            "SELECT payload_sha256,payload_json FROM evidence_lifecycle_events WHERE lifecycle_event_id=?",
            (str(event.lifecycle_event_id),),
        ).fetchone()
        if row is not None:
            if row["payload_sha256"] != digest:
                raise ValueError("evidence lifecycle identity conflict")
            return EvidenceLifecycleEvent.model_validate(json.loads(row["payload_json"]))
        latest = self._connection.execute(
            "SELECT payload_json FROM evidence_lifecycle_events WHERE evidence_id=? ORDER BY resulting_version DESC LIMIT 1",
            (str(event.evidence_id),),
        ).fetchone()
        current_version = 0
        current_state = None
        if latest is not None:
            current = EvidenceLifecycleEvent.model_validate(json.loads(latest["payload_json"]))
            current_version = current.resulting_version
            current_state = current.to_state
        if event.expected_version != current_version or event.from_state != current_state:
            raise ValueError("evidence lifecycle stale version or state")
        self._append_authority(
            AuthorityMutationKind.EVIDENCE_LIFECYCLE,
            str(event.lifecycle_event_id),
            event.created_at,
            payload,
        )
        self._connection.execute(
            """INSERT INTO evidence_lifecycle_events(
               lifecycle_event_id,evidence_id,incident_id,action,from_state,to_state,expected_version,
               resulting_version,created_at,payload_sha256,payload_json
               ) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(event.lifecycle_event_id), str(event.evidence_id), str(event.incident_id), event.action.value,
                event.from_state.value if event.from_state else None, event.to_state.value, event.expected_version,
                event.resulting_version, event.created_at.isoformat(), digest, event.model_dump_json(),
            ),
        )
        return event

    def record_evidence_lifecycle(self, event: EvidenceLifecycleEvent) -> EvidenceLifecycleEvent:
        with self._lock, self._connection:
            exists = self._connection.execute(
                "SELECT incident_id FROM evidence_items WHERE evidence_id=?", (str(event.evidence_id),)
            ).fetchone()
            if exists is None or exists["incident_id"] != str(event.incident_id):
                raise ValueError("evidence lifecycle target does not exist or incident differs")
            return self._record_evidence_lifecycle_locked(event)

    def evidence_lifecycle_events(self, evidence_id: str | None = None, incident_id: str | None = None) -> tuple[EvidenceLifecycleEvent, ...]:
        if evidence_id is not None:
            rows = self._connection.execute(
                "SELECT payload_json FROM evidence_lifecycle_events WHERE evidence_id=? ORDER BY resulting_version",
                (evidence_id,),
            ).fetchall()
        elif incident_id is not None:
            rows = self._connection.execute(
                "SELECT payload_json FROM evidence_lifecycle_events WHERE incident_id=? ORDER BY created_at,lifecycle_event_id",
                (incident_id,),
            ).fetchall()
        else:
            rows = self._connection.execute(
                "SELECT payload_json FROM evidence_lifecycle_events ORDER BY created_at,lifecycle_event_id"
            ).fetchall()
        return tuple(EvidenceLifecycleEvent.model_validate(json.loads(row[0])) for row in rows)

    def evidence_lifecycle_projection(self, evidence_id: str) -> EvidenceLifecycleProjection:
        item_row = self._connection.execute(
            "SELECT payload_json FROM evidence_items WHERE evidence_id=?", (evidence_id,)
        ).fetchone()
        if item_row is None:
            raise KeyError(evidence_id)
        item = EvidenceItem.model_validate(json.loads(item_row["payload_json"]))
        events = self.evidence_lifecycle_events(evidence_id=evidence_id)
        if not events:
            raise RuntimeError("evidence lifecycle is missing")
        last = events[-1]
        state = last.to_state
        rights_active = item.rights_expires_at is None or item.rights_expires_at > datetime.now(timezone.utc)
        readable = state is EvidenceContentState.AVAILABLE and rights_active
        claim_eligible = state in {EvidenceContentState.AVAILABLE, EvidenceContentState.METADATA_ONLY, EvidenceContentState.REDACTED} and rights_active
        return EvidenceLifecycleProjection(
            evidence_id=item.evidence_id,
            incident_id=item.incident_id,
            state=state,
            version=last.resulting_version,
            readable=readable,
            claim_eligible=claim_eligible,
            rights_active=rights_active,
            deletion_proven=state is EvidenceContentState.DELETED and bool(last.deletion_proof_sha256),
            last_event_id=last.lifecycle_event_id,
            updated_at=last.created_at,
            reason_codes=last.reason_codes,
        )

    def record_media_parser_report(self, report: MediaParserReport) -> MediaParserReport:
        payload = report.model_dump(mode="json")
        digest = sha256_bytes(canonical_json_bytes(payload))
        with self._lock, self._connection:
            row = self._connection.execute(
                "SELECT payload_sha256,payload_json FROM media_parser_runs WHERE parse_id=?",
                (str(report.parse_id),),
            ).fetchone()
            if row is not None:
                if row["payload_sha256"] != digest:
                    raise ValueError("media parser report identity conflict")
                return MediaParserReport.model_validate(json.loads(row["payload_json"]))
            self._append_authority(AuthorityMutationKind.MEDIA_PARSE, str(report.parse_id), report.created_at, payload)
            self._connection.execute(
                """INSERT INTO media_parser_runs(
                   parse_id,input_sha256,output_sha256,status,created_at,payload_sha256,payload_json
                   ) VALUES (?,?,?,?,?,?,?)""",
                (str(report.parse_id), report.input_sha256, report.output_sha256, report.status.value,
                 report.created_at.isoformat(), digest, report.model_dump_json()),
            )
            return report

    def media_parser_reports(self) -> tuple[MediaParserReport, ...]:
        rows = self._connection.execute(
            "SELECT payload_json FROM media_parser_runs ORDER BY created_at,parse_id"
        ).fetchall()
        return tuple(MediaParserReport.model_validate(json.loads(row[0])) for row in rows)

    def record_evidence_reevaluation(self, record: EvidenceReevaluationRecord) -> EvidenceReevaluationRecord:
        payload = record.model_dump(mode="json")
        digest = sha256_bytes(canonical_json_bytes(payload))
        with self._lock, self._connection:
            row = self._connection.execute(
                "SELECT payload_sha256,payload_json FROM evidence_reevaluations WHERE reevaluation_id=?",
                (str(record.reevaluation_id),),
            ).fetchone()
            if row is not None:
                if row["payload_sha256"] != digest:
                    raise ValueError("evidence reevaluation identity conflict")
                return EvidenceReevaluationRecord.model_validate(json.loads(row["payload_json"]))
            self._append_authority(
                AuthorityMutationKind.EVIDENCE_REEVALUATION, str(record.reevaluation_id), record.created_at, payload
            )
            self._connection.execute(
                """INSERT INTO evidence_reevaluations(
                   reevaluation_id,incident_id,evidence_id,trigger_action,status,created_at,payload_sha256,payload_json
                   ) VALUES (?,?,?,?,?,?,?,?)""",
                (str(record.reevaluation_id), str(record.incident_id), str(record.evidence_id),
                 record.trigger_action.value, record.status, record.created_at.isoformat(), digest, record.model_dump_json()),
            )
            return record

    def evidence_reevaluations(self, incident_id: str | None = None) -> tuple[EvidenceReevaluationRecord, ...]:
        if incident_id is None:
            rows = self._connection.execute(
                "SELECT payload_json FROM evidence_reevaluations ORDER BY created_at,reevaluation_id"
            ).fetchall()
        else:
            rows = self._connection.execute(
                "SELECT payload_json FROM evidence_reevaluations WHERE incident_id=? ORDER BY created_at,reevaluation_id",
                (incident_id,),
            ).fetchall()
        return tuple(EvidenceReevaluationRecord.model_validate(json.loads(row[0])) for row in rows)

    def record_claim(self, claim: ClaimNode) -> ClaimNode:
        payload = claim.model_dump(mode="json")
        digest = sha256_bytes(canonical_json_bytes(payload))
        with self._lock, self._connection:
            row = self._connection.execute(
                "SELECT payload_sha256,payload_json FROM claim_nodes WHERE claim_id=?", (str(claim.claim_id),)
            ).fetchone()
            if row is not None:
                if row["payload_sha256"] != digest:
                    raise ValueError("claim identity conflict")
                return ClaimNode.model_validate(json.loads(row["payload_json"]))
            self._append_authority(AuthorityMutationKind.CLAIM, str(claim.claim_id), claim.created_at, payload)
            self._connection.execute(
                """INSERT INTO claim_nodes(
                   claim_id,incident_id,hazard,status,created_at,payload_sha256,payload_json
                   ) VALUES (?,?,?,?,?,?,?)""",
                (str(claim.claim_id), str(claim.incident_id), claim.hazard.value, claim.status,
                 claim.created_at.isoformat(), digest, claim.model_dump_json()),
            )
            return claim

    def claims(self, incident_id: str | None = None) -> tuple[ClaimNode, ...]:
        if incident_id is None:
            rows = self._connection.execute(
                "SELECT payload_json FROM claim_nodes ORDER BY created_at,claim_id"
            ).fetchall()
        else:
            rows = self._connection.execute(
                "SELECT payload_json FROM claim_nodes WHERE incident_id=? ORDER BY created_at,claim_id",
                (incident_id,),
            ).fetchall()
        return tuple(ClaimNode.model_validate(json.loads(row[0])) for row in rows)

    def record_claim_link(self, link: ClaimEvidenceLink) -> ClaimEvidenceLink:
        payload = link.model_dump(mode="json")
        digest = sha256_bytes(canonical_json_bytes(payload))
        with self._lock, self._connection:
            claim = self._connection.execute("SELECT 1 FROM claim_nodes WHERE claim_id=?", (str(link.claim_id),)).fetchone()
            evidence = self._connection.execute("SELECT 1 FROM evidence_items WHERE evidence_id=?", (str(link.evidence_id),)).fetchone()
            if claim is None or evidence is None:
                raise ValueError("claim link target does not exist")
            row = self._connection.execute(
                "SELECT payload_sha256,payload_json FROM claim_evidence_links WHERE claim_id=? AND evidence_id=? AND relation=?",
                (str(link.claim_id), str(link.evidence_id), link.relation.value),
            ).fetchone()
            if row is not None:
                if row["payload_sha256"] != digest:
                    raise ValueError("claim link identity conflict")
                return ClaimEvidenceLink.model_validate(json.loads(row["payload_json"]))
            self._append_authority(AuthorityMutationKind.CLAIM_LINK, str(link.link_id), link.created_at, payload)
            self._connection.execute(
                """INSERT INTO claim_evidence_links(
                   link_id,claim_id,evidence_id,relation,created_at,payload_sha256,payload_json
                   ) VALUES (?,?,?,?,?,?,?)""",
                (str(link.link_id), str(link.claim_id), str(link.evidence_id), link.relation.value,
                 link.created_at.isoformat(), digest, link.model_dump_json()),
            )
            return link

    def claim_links(self, incident_id: str | None = None) -> tuple[ClaimEvidenceLink, ...]:
        if incident_id is None:
            rows = self._connection.execute(
                "SELECT payload_json FROM claim_evidence_links ORDER BY created_at,link_id"
            ).fetchall()
        else:
            rows = self._connection.execute(
                """SELECT l.payload_json FROM claim_evidence_links l
                   JOIN claim_nodes c ON c.claim_id=l.claim_id
                   WHERE c.incident_id=? ORDER BY l.created_at,l.link_id""",
                (incident_id,),
            ).fetchall()
        return tuple(ClaimEvidenceLink.model_validate(json.loads(row[0])) for row in rows)

    def record_incident_relation(self, relation: IncidentRelation) -> IncidentRelation:
        payload = relation.model_dump(mode="json")
        digest = sha256_bytes(canonical_json_bytes(payload))
        with self._lock, self._connection:
            row = self._connection.execute(
                """SELECT payload_sha256,payload_json FROM incident_relations
                   WHERE source_incident_id=? AND target_incident_id=? AND relation=?""",
                (str(relation.source_incident_id), str(relation.target_incident_id), relation.relation.value),
            ).fetchone()
            if row is not None:
                if row["payload_sha256"] != digest:
                    raise ValueError("incident relation conflict")
                return IncidentRelation.model_validate(json.loads(row["payload_json"]))
            self._append_authority(
                AuthorityMutationKind.INCIDENT_RELATION, str(relation.relation_id), relation.created_at, payload
            )
            self._connection.execute(
                """INSERT INTO incident_relations(
                   relation_id,source_incident_id,source_hazard,target_incident_id,target_hazard,relation,
                   created_at,payload_sha256,payload_json
                   ) VALUES (?,?,?,?,?,?,?,?,?)""",
                (str(relation.relation_id), str(relation.source_incident_id), relation.source_hazard.value,
                 str(relation.target_incident_id), relation.target_hazard.value, relation.relation.value,
                 relation.created_at.isoformat(), digest, relation.model_dump_json()),
            )
            return relation

    def incident_relations(self) -> tuple[IncidentRelation, ...]:
        rows = self._connection.execute(
            "SELECT payload_json FROM incident_relations ORDER BY created_at,relation_id"
        ).fetchall()
        return tuple(IncidentRelation.model_validate(json.loads(row[0])) for row in rows)

    def record_identity_decision(
        self, candidate: IncidentCandidate, decision: IncidentIdentityDecision
    ) -> IncidentIdentityDecision:
        candidate_payload = candidate.model_dump(mode="json")
        decision_payload = decision.model_dump(mode="json")
        candidate_digest = sha256_bytes(canonical_json_bytes(candidate_payload))
        decision_digest = sha256_bytes(canonical_json_bytes(decision_payload))
        with self._lock, self._connection:
            existing = self._connection.execute(
                "SELECT payload_sha256,payload_json FROM incident_identity_decisions WHERE candidate_id=?",
                (str(candidate.candidate_id),),
            ).fetchone()
            if existing is not None:
                if existing["payload_sha256"] != decision_digest:
                    raise ValueError("incident identity decision conflict")
                return IncidentIdentityDecision.model_validate(json.loads(existing["payload_json"]))
            self._connection.execute(
                """INSERT INTO incident_candidates(
                   candidate_id,incident_id,hazard,observed_at,latitude,longitude,source_id,source_event_id,payload_sha256,payload_json
                   ) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (str(candidate.candidate_id), str(decision.incident_id), candidate.hazard.value,
                 candidate.observed_at.isoformat(), candidate.latitude, candidate.longitude, candidate.source_id,
                 candidate.source_event_id, candidate_digest, candidate.model_dump_json()),
            )
            self._connection.execute(
                """INSERT INTO incident_identity_decisions(
                   decision_id,candidate_id,incident_id,outcome,decided_at,payload_sha256,payload_json
                   ) VALUES (?,?,?,?,?,?,?)""",
                (str(decision.decision_id), str(decision.candidate_id), str(decision.incident_id),
                 decision.outcome.value, decision.decided_at.isoformat(), decision_digest, decision.model_dump_json()),
            )
            return decision

    def incident_candidates(self, hazard: str | None = None) -> tuple[tuple[IncidentCandidate, str], ...]:
        if hazard is None:
            rows = self._connection.execute(
                "SELECT payload_json,incident_id FROM incident_candidates ORDER BY observed_at,candidate_id"
            ).fetchall()
        else:
            rows = self._connection.execute(
                "SELECT payload_json,incident_id FROM incident_candidates WHERE hazard=? ORDER BY observed_at,candidate_id",
                (hazard,),
            ).fetchall()
        return tuple((IncidentCandidate.model_validate(json.loads(row["payload_json"])), row["incident_id"]) for row in rows)

    def identity_decisions(self) -> tuple[IncidentIdentityDecision, ...]:
        rows = self._connection.execute(
            "SELECT payload_json FROM incident_identity_decisions ORDER BY decided_at,decision_id"
        ).fetchall()
        return tuple(IncidentIdentityDecision.model_validate(json.loads(row[0])) for row in rows)

    def authority_conformance(self) -> dict[str, object]:
        rows = self._connection.execute(
            """SELECT a.position,a.epoch_id,a.epoch_ordinal,a.predecessor_position,a.kind,a.entity_id,
                      a.payload_sha256,a.payload_json,s.kind AS subtype_kind,s.subtype_id,
                      s.payload_sha256 AS subtype_sha256,s.payload_json AS subtype_payload
               FROM authority_events a LEFT JOIN authority_event_subtypes s
                 ON s.authority_position=a.position ORDER BY a.position"""
        ).fetchall()
        failures: list[str] = []
        previous_position: int | None = None
        for expected_ordinal, row in enumerate(rows, start=1):
            position = int(row["position"])
            if row["epoch_id"] != "authority-epoch-1":
                failures.append(f"wrong_epoch:{position}")
            if int(row["epoch_ordinal"] or -1) != expected_ordinal:
                failures.append(f"ordinal_gap:{position}")
            if row["predecessor_position"] != previous_position:
                failures.append(f"predecessor_mismatch:{position}")
            if row["subtype_kind"] is None:
                failures.append(f"missing_subtype:{position}")
            elif row["subtype_kind"] != row["kind"] or row["subtype_id"] != row["entity_id"]:
                failures.append(f"subtype_identity_mismatch:{position}")
            payload = json.loads(row["payload_json"])
            digest = sha256_bytes(canonical_json_bytes(payload))
            if row["payload_sha256"] != digest:
                failures.append(f"supertype_digest_mismatch:{position}")
            if row["subtype_sha256"] != digest or row["subtype_payload"] != row["payload_json"]:
                failures.append(f"subtype_digest_mismatch:{position}")
            previous_position = position
        orphan_count = int(self._connection.execute(
            """SELECT COUNT(*) FROM authority_event_subtypes s LEFT JOIN authority_events a
               ON a.position=s.authority_position WHERE a.position IS NULL"""
        ).fetchone()[0])
        if orphan_count:
            failures.append(f"orphan_subtypes:{orphan_count}")
        watermark = previous_position or 0
        return {
            "valid": not failures,
            "epoch_id": "authority-epoch-1",
            "event_count": len(rows),
            "highest_contiguous_position": watermark if not failures else 0,
            "failures": tuple(failures),
        }

    def checkpoint(self, mode: str = "PASSIVE") -> dict[str, int | float | str]:
        import time

        allowed = {"PASSIVE", "FULL", "RESTART", "TRUNCATE"}
        mode = mode.upper()
        if mode not in allowed:
            raise ValueError(f"unsupported checkpoint mode: {mode}")
        started = time.perf_counter_ns()
        with self._lock:
            row = self._connection.execute(f"PRAGMA wal_checkpoint({mode})").fetchone()
        duration_ms = (time.perf_counter_ns() - started) / 1_000_000
        return {
            "mode": mode,
            "busy": int(row[0]),
            "log_frames": int(row[1]),
            "checkpointed_frames": int(row[2]),
            "duration_ms": duration_ms,
        }

    def integrity_check(self) -> str:
        with self._lock:
            return str(self._connection.execute("PRAGMA integrity_check").fetchone()[0])

    def durability_profile(self) -> dict[str, object]:
        synchronous = int(self._connection.execute("PRAGMA synchronous").fetchone()[0])
        journal_mode = str(self._connection.execute("PRAGMA journal_mode").fetchone()[0])
        return {
            "journal_mode": journal_mode,
            "synchronous": synchronous,
            "critical_truth_full_durability": synchronous == 2 and journal_mode.lower() == "wal",
        }

    def close(self) -> None:
        self._connection.close()


class ConfigurationStore:
    """Durable configuration staging, active/LKG pointers, and activation history."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=FULL")
        self._connection.execute("PRAGMA busy_timeout=5000")
        self._connection.row_factory = sqlite3.Row
        self._lock = RLock()
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS configuration_bundles (
                bundle_key TEXT PRIMARY KEY,
                bundle_id TEXT NOT NULL,
                version TEXT NOT NULL,
                state TEXT NOT NULL,
                bundle_sha256 TEXT NOT NULL,
                artifact_ref TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(bundle_id,version)
            );
            CREATE TABLE IF NOT EXISTS configuration_activations (
                activation_id TEXT PRIMARY KEY,
                bundle_key TEXT NOT NULL,
                state TEXT NOT NULL,
                accepted_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS configuration_pointers (
                singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                active_bundle_key TEXT,
                last_known_good_bundle_key TEXT
            );
            INSERT OR IGNORE INTO configuration_pointers(singleton) VALUES (1);
            """
        )

    @staticmethod
    def key(bundle: ConfigurationBundle) -> str:
        return f"{bundle.bundle_id}@{bundle.version}"

    def stage(self, bundle: ConfigurationBundle, *, bundle_sha256: str, artifact_ref: str) -> None:
        key = self.key(bundle)
        with self._lock, self._connection:
            existing = self._connection.execute(
                "SELECT bundle_sha256 FROM configuration_bundles WHERE bundle_key=?", (key,)
            ).fetchone()
            if existing is not None:
                if existing["bundle_sha256"] != bundle_sha256:
                    raise ValueError("configuration identity is immutable")
                return
            self._connection.execute(
                """
                INSERT INTO configuration_bundles(
                    bundle_key,bundle_id,version,state,bundle_sha256,artifact_ref,payload_json,created_at
                ) VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    key,
                    bundle.bundle_id,
                    bundle.version,
                    ConfigurationState.STAGED.value,
                    bundle_sha256,
                    artifact_ref,
                    bundle.model_dump_json(),
                    bundle.created_at.isoformat(),
                ),
            )

    def _bundle_for_key(self, key: str | None) -> ConfigurationBundle | None:
        if key is None:
            return None
        row = self._connection.execute(
            "SELECT payload_json FROM configuration_bundles WHERE bundle_key=?", (key,)
        ).fetchone()
        return ConfigurationBundle.model_validate(json.loads(row[0])) if row else None

    def active(self) -> ConfigurationBundle | None:
        row = self._connection.execute(
            "SELECT active_bundle_key FROM configuration_pointers WHERE singleton=1"
        ).fetchone()
        return self._bundle_for_key(row[0] if row else None)

    def last_known_good(self) -> ConfigurationBundle | None:
        row = self._connection.execute(
            "SELECT last_known_good_bundle_key FROM configuration_pointers WHERE singleton=1"
        ).fetchone()
        return self._bundle_for_key(row[0] if row else None)

    def _insert_activation(self, activation: ConfigurationActivationRecord) -> None:
        key = f"{activation.bundle_id}@{activation.version}"
        self._connection.execute(
            """
            INSERT INTO configuration_activations(activation_id,bundle_key,state,accepted_at,payload_json)
            VALUES (?,?,?,?,?)
            """,
            (
                str(activation.activation_id),
                key,
                activation.state.value,
                activation.activated_at.isoformat(),
                activation.model_dump_json(),
            ),
        )
        self._connection.execute(
            "UPDATE configuration_bundles SET state=? WHERE bundle_key=?",
            (activation.state.value, key),
        )

    def record(self, activation: ConfigurationActivationRecord) -> None:
        with self._lock, self._connection:
            self._insert_activation(activation)

    def activate(self, bundle: ConfigurationBundle, activation: ConfigurationActivationRecord) -> None:
        key = self.key(bundle)
        with self._lock, self._connection:
            pointer = self._connection.execute(
                "SELECT active_bundle_key FROM configuration_pointers WHERE singleton=1"
            ).fetchone()
            previous = pointer[0] if pointer else None
            if previous and previous != key:
                self._connection.execute(
                    "UPDATE configuration_bundles SET state=? WHERE bundle_key=?",
                    (ConfigurationState.LAST_KNOWN_GOOD.value, previous),
                )
            self._insert_activation(activation)
            self._connection.execute(
                """
                UPDATE configuration_pointers
                SET active_bundle_key=?,last_known_good_bundle_key=? WHERE singleton=1
                """,
                (key, previous if previous != key else self.last_known_good_key()),
            )

    def last_known_good_key(self) -> str | None:
        row = self._connection.execute(
            "SELECT last_known_good_bundle_key FROM configuration_pointers WHERE singleton=1"
        ).fetchone()
        return row[0] if row else None

    def rollback(
        self,
        candidate: ConfigurationBundle,
        previous: ConfigurationBundle | None,
        activation: ConfigurationActivationRecord,
    ) -> None:
        candidate_key = self.key(candidate)
        previous_key = self.key(previous) if previous else None
        with self._lock, self._connection:
            self._insert_activation(activation)
            if previous_key:
                self._connection.execute(
                    "UPDATE configuration_bundles SET state=? WHERE bundle_key=?",
                    (ConfigurationState.ACTIVE.value, previous_key),
                )
            self._connection.execute(
                """
                UPDATE configuration_pointers
                SET active_bundle_key=?,last_known_good_bundle_key=? WHERE singleton=1
                """,
                (previous_key, previous_key),
            )
            self._connection.execute(
                "UPDATE configuration_bundles SET state=? WHERE bundle_key=?",
                (ConfigurationState.ROLLED_BACK.value, candidate_key),
            )

    def activation_records(self) -> tuple[ConfigurationActivationRecord, ...]:
        rows = self._connection.execute(
            "SELECT payload_json FROM configuration_activations ORDER BY accepted_at,activation_id"
        ).fetchall()
        return tuple(ConfigurationActivationRecord.model_validate(json.loads(row[0])) for row in rows)

    def state(self) -> dict:
        active = self.active()
        lkg = self.last_known_good()
        return {
            "active": active.model_dump(mode="json") if active else None,
            "last_known_good": lkg.model_dump(mode="json") if lkg else None,
            "history": [item.model_dump(mode="json") for item in self.activation_records()],
        }

    def close(self) -> None:
        self._connection.close()


class SourceCursorStore:
    """Component-1-owned durable sequence, boot, clock-epoch, and event-time watermarks."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=FULL")
        self._connection.execute("PRAGMA busy_timeout=5000")
        self._connection.row_factory = sqlite3.Row
        self._lock = RLock()
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS source_cursors (
                source_id TEXT PRIMARY KEY,
                boot_id TEXT NOT NULL,
                clock_epoch INTEGER NOT NULL,
                last_sequence INTEGER NOT NULL,
                last_observed_at TEXT NOT NULL,
                clock_uncertainty_ms REAL NOT NULL DEFAULT 0,
                state TEXT NOT NULL,
                reason_codes_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS source_health_events (
                event_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                previous_state TEXT,
                state TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                boot_id TEXT,
                sequence INTEGER,
                reason_codes_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_source_health_events_source_time
                ON source_health_events(source_id,recorded_at);
            """
        )
        columns = {row[1] for row in self._connection.execute("PRAGMA table_info(source_cursors)").fetchall()}
        if "clock_uncertainty_ms" not in columns:
            self._connection.execute("ALTER TABLE source_cursors ADD COLUMN clock_uncertainty_ms REAL NOT NULL DEFAULT 0")
        event_columns = {row[1] for row in self._connection.execute("PRAGMA table_info(source_health_events)").fetchall()}
        if "clock_uncertainty_ms" not in event_columns:
            self._connection.execute("ALTER TABLE source_health_events ADD COLUMN clock_uncertainty_ms REAL NOT NULL DEFAULT 0")

    def load_all(self) -> tuple[SourceHealth, ...]:
        rows = self._connection.execute(
            "SELECT source_id,boot_id,clock_epoch,last_sequence,last_observed_at,clock_uncertainty_ms,state,reason_codes_json FROM source_cursors ORDER BY source_id"
        ).fetchall()
        return tuple(
            SourceHealth(
                source_id=row[0],
                boot_id=row[1],
                clock_epoch=row[2],
                last_sequence=row[3],
                last_observed_at=datetime.fromisoformat(row[4]),
                event_time_watermark=datetime.fromisoformat(row[4]),
                clock_uncertainty_ms=row[5],
                state=row[6],
                reason_codes=tuple(json.loads(row[7])),
            )
            for row in rows
        )

    def upsert(self, health: SourceHealth, *, recorded_at: datetime | None = None) -> None:
        if health.boot_id is None or health.clock_epoch is None or health.last_sequence is None or health.last_observed_at is None:
            raise ValueError("complete source cursor required")
        with self._lock, self._connection:
            previous = self._connection.execute(
                "SELECT state,reason_codes_json FROM source_cursors WHERE source_id=?", (health.source_id,)
            ).fetchone()
            self._connection.execute(
                """
                INSERT INTO source_cursors(source_id,boot_id,clock_epoch,last_sequence,last_observed_at,clock_uncertainty_ms,state,reason_codes_json)
                VALUES (?,?,?,?,?,?,?,?)
                ON CONFLICT(source_id) DO UPDATE SET
                    boot_id=excluded.boot_id,
                    clock_epoch=excluded.clock_epoch,
                    last_sequence=excluded.last_sequence,
                    last_observed_at=excluded.last_observed_at,
                    clock_uncertainty_ms=excluded.clock_uncertainty_ms,
                    state=excluded.state,
                    reason_codes_json=excluded.reason_codes_json
                """,
                (
                    health.source_id,
                    health.boot_id,
                    health.clock_epoch,
                    health.last_sequence,
                    health.last_observed_at.isoformat(),
                    health.clock_uncertainty_ms,
                    health.state.value,
                    json.dumps(list(health.reason_codes), sort_keys=True),
                ),
            )
            previous_state = previous[0] if previous else None
            previous_reasons = tuple(json.loads(previous[1])) if previous else ()
            if previous is None or previous_state != health.state.value or previous_reasons != health.reason_codes:
                event_key = ":".join(
                    [
                        health.source_id,
                        previous_state or "none",
                        health.state.value,
                        str(health.last_sequence),
                        (recorded_at or health.last_observed_at).isoformat(),
                        ",".join(health.reason_codes),
                    ]
                )
                event = SourceHealthEvent(
                    event_id=uuid5(NAMESPACE_URL, f"sentinel-source-health:{event_key}"),
                    source_id=health.source_id,
                    previous_state=previous_state,
                    state=health.state,
                    recorded_at=recorded_at or health.last_observed_at,
                    boot_id=health.boot_id,
                    sequence=health.last_sequence,
                    clock_uncertainty_ms=health.clock_uncertainty_ms,
                    reason_codes=health.reason_codes,
                )
                self._connection.execute(
                    """
                    INSERT INTO source_health_events(
                        event_id,source_id,previous_state,state,recorded_at,boot_id,sequence,clock_uncertainty_ms,reason_codes_json
                    ) VALUES (?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        str(event.event_id),
                        event.source_id,
                        event.previous_state.value if event.previous_state else None,
                        event.state.value,
                        event.recorded_at.isoformat(),
                        event.boot_id,
                        event.sequence,
                        event.clock_uncertainty_ms,
                        json.dumps(list(event.reason_codes), sort_keys=True),
                    ),
                )

    def events(self) -> tuple[SourceHealthEvent, ...]:
        rows = self._connection.execute(
            "SELECT * FROM source_health_events ORDER BY recorded_at,event_id"
        ).fetchall()
        return tuple(
            SourceHealthEvent(
                event_id=row["event_id"],
                source_id=row["source_id"],
                previous_state=row["previous_state"],
                state=row["state"],
                recorded_at=datetime.fromisoformat(row["recorded_at"]),
                boot_id=row["boot_id"],
                sequence=row["sequence"],
                reason_codes=tuple(json.loads(row["reason_codes_json"])),
            )
            for row in rows
        )

    def close(self) -> None:
        self._connection.close()
