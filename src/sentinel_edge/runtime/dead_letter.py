"""Bounded immutable dead-letter and redrive contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any


@dataclass(frozen=True)
class DeadLetterRecord:
    record_id: str
    envelope: dict[str, Any]
    payload_sha256: str
    reason: str
    attempts: int
    validity: str
    aggregate: str
    destination: str
    causation_id: str
    correlation_id: str
    idempotency_key: str


@dataclass
class DeadLetterStore:
    max_attempts: int = 3
    max_records: int = 1000
    _records: dict[str, DeadLetterRecord] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.max_attempts <= 0 or self.max_records <= 0:
            raise ValueError("dead-letter bounds must be positive")

    def record(self, *, record_id: str, envelope: dict[str, Any], payload: bytes,
               reason: str, attempts: int, validity: str, aggregate: str,
               destination: str, causation_id: str, correlation_id: str,
               idempotency_key: str) -> DeadLetterRecord:
        if not record_id.strip() or not reason.strip() or not aggregate.strip() or not destination.strip():
            raise ValueError("dead-letter identity and reason are required")
        if attempts < 1 or attempts > self.max_attempts:
            raise ValueError("dead-letter attempts exceed policy")
        if record_id in self._records:
            return self._records[record_id]
        if len(self._records) >= self.max_records:
            raise OverflowError("dead-letter capacity exhausted")
        item = DeadLetterRecord(record_id, dict(envelope), sha256(payload).hexdigest(), reason,
            attempts, validity, aggregate, destination, causation_id, correlation_id, idempotency_key)
        self._records[record_id] = item
        return item

    def redrive(self, record_id: str, *, current_valid: bool, target_version: int) -> dict[str, Any]:
        item = self._records[record_id]
        if not current_valid or target_version < 0:
            raise PermissionError("dead-letter redrive revalidation failed")
        return {"record_id": item.record_id, "attempt": item.attempts + 1,
                "causation_id": item.causation_id, "correlation_id": item.correlation_id,
                "idempotency_key": item.idempotency_key, "target_version": target_version}
