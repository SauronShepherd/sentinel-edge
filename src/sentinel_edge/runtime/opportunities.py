from __future__ import annotations

import hashlib
import json
import base64
from collections import Counter
from datetime import datetime
from uuid import NAMESPACE_URL, UUID, uuid5
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from sentinel_edge.security import canonical_json_bytes, sha256_bytes
from sentinel_edge.update import key_id

from sentinel_edge.domain.models import HazardKind, OpportunityDisposition, OpportunityRecord


class OpportunityLedger:
    """Records offered work before scheduling and reconciles every terminal disposition."""

    def __init__(self) -> None:
        self._records: dict[UUID, OpportunityRecord] = {}

    def offer(
        self,
        *,
        workload_id: str,
        hazard: HazardKind,
        scheduled_release_at: datetime,
        captured_at: datetime | None,
        correlation_id: UUID,
    ) -> OpportunityRecord:
        opportunity_id = uuid5(
            NAMESPACE_URL,
            f"sentinel-opportunity:{correlation_id}:{workload_id}:{scheduled_release_at.isoformat()}",
        )
        record = OpportunityRecord(
            opportunity_id=opportunity_id,
            workload_id=workload_id,
            hazard=hazard,
            scheduled_release_at=scheduled_release_at,
            captured_at=captured_at,
            correlation_id=correlation_id,
        )
        self._records[record.opportunity_id] = record
        return record

    def mark_queued(self, opportunity_id: UUID, actual_release_at: datetime, queue_ns: int, deadline_ns: int) -> None:
        record = self._records[opportunity_id]
        record.actual_release_at = actual_release_at
        record.queue_started_monotonic_ns = queue_ns
        record.deadline_monotonic_ns = deadline_ns
        record.disposition = OpportunityDisposition.QUEUED

    def mark_deferred(self, opportunity_id: UUID, reason: str) -> None:
        record = self._records[opportunity_id]
        record.disposition = OpportunityDisposition.DEFERRED
        if reason not in record.reason_codes:
            record.reason_codes.append(reason)

    def mark_started(self, opportunity_id: UUID, service_ns: int) -> None:
        record = self._records[opportunity_id]
        record.service_started_monotonic_ns = service_ns

    def mark_terminal(self, opportunity_id: UUID, disposition: OpportunityDisposition, completed_ns: int, reason: str | None = None) -> None:
        if disposition not in {
            OpportunityDisposition.PROCESSED,
            OpportunityDisposition.SKIPPED,
            OpportunityDisposition.REPLACED,
            OpportunityDisposition.INVALID,
            OpportunityDisposition.DROPPED,
            OpportunityDisposition.EXPIRED,
            OpportunityDisposition.FAILED,
            OpportunityDisposition.DEADLINE_MISSED,
        }:
            raise ValueError("terminal opportunity disposition required")
        record = self._records[opportunity_id]
        record.completed_monotonic_ns = completed_ns
        record.disposition = disposition
        if reason and reason not in record.reason_codes:
            record.reason_codes.append(reason)

    def records(self) -> tuple[OpportunityRecord, ...]:
        return tuple(sorted(self._records.values(), key=lambda item: (item.scheduled_release_at, str(item.opportunity_id))))

    def counts(self) -> dict[str, int]:
        counts = Counter(record.disposition.value for record in self._records.values())
        # ``offered`` is an opportunity total, not a terminal disposition.
        # Keeping it separate prevents a fully processed run from reporting
        # zero offered work in the public scenario transcript.
        return {
            "offered": len(self._records),
            **{
                name: counts.get(name, 0)
                for name in OpportunityDisposition
                if name != OpportunityDisposition.OFFERED.value
            },
        }

    def reconcile(self) -> dict[str, int | bool]:
        terminal = {
            OpportunityDisposition.PROCESSED,
            OpportunityDisposition.SKIPPED,
            OpportunityDisposition.REPLACED,
            OpportunityDisposition.INVALID,
            OpportunityDisposition.DROPPED,
            OpportunityDisposition.EXPIRED,
            OpportunityDisposition.FAILED,
            OpportunityDisposition.DEADLINE_MISSED,
        }
        offered = len(self._records)
        terminal_count = sum(1 for item in self._records.values() if item.disposition in terminal)
        return {"offered": offered, "terminal": terminal_count, "balanced": offered == terminal_count}

    def schedule_digest(self) -> str:
        raw = canonical_json_bytes(self._schedule_payload())
        return hashlib.sha256(raw).hexdigest()

    def _schedule_payload(self) -> list[dict[str, str | None]]:
        return [
            {
                "correlation_id": str(item.correlation_id),
                "workload_id": item.workload_id,
                "hazard": item.hazard.value,
                "scheduled_release_at": item.scheduled_release_at.isoformat(),
                "captured_at": item.captured_at.isoformat() if item.captured_at else None,
            }
            for item in self.records()
        ]

    def sign_schedule(self, private_key: Ed25519PrivateKey) -> dict[str, object]:
        payload = self._schedule_payload()
        raw = canonical_json_bytes(payload)
        return {
            "schema": "sentinel-edge-opportunity-schedule/1.0",
            "schedule": payload,
            "schedule_sha256": sha256_bytes(raw),
            "signer_key_id": key_id(private_key.public_key()),
            "algorithm": "Ed25519",
            "signature": base64.b64encode(private_key.sign(raw)).decode("ascii"),
        }

    @staticmethod
    def verify_signed_schedule(envelope: dict[str, object], public_key: Ed25519PublicKey) -> dict[str, object]:
        schedule = envelope.get("schedule")
        raw = canonical_json_bytes(schedule)
        failures: list[str] = []
        if envelope.get("schema") != "sentinel-edge-opportunity-schedule/1.0":
            failures.append("schedule_schema_invalid")
        if envelope.get("algorithm") != "Ed25519":
            failures.append("unsupported_signature_algorithm")
        if envelope.get("signer_key_id") != key_id(public_key):
            failures.append("signer_key_id_mismatch")
        if envelope.get("schedule_sha256") != sha256_bytes(raw):
            failures.append("schedule_digest_mismatch")
        try:
            public_key.verify(base64.b64decode(str(envelope.get("signature", "")), validate=True), raw)
        except (ValueError, InvalidSignature):
            failures.append("signature_invalid")
        return {"valid": not failures, "schedule_sha256": sha256_bytes(raw), "failures": failures}
