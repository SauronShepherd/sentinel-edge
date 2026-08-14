from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sentinel_edge.domain.models import EvidenceLifecycleAction, EvidenceLifecycleEvent
from sentinel_edge.security import canonical_json_bytes, sha256_bytes


class TombstoneJournal(BaseModel):
    """Minimal, non-content lifecycle journal used to prevent data resurrection."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True)

    schema_: str = Field(default="sentinel-edge-privacy-tombstones/1.0", alias="schema")
    journal_id: UUID
    generated_at: datetime
    source_authority_position: int = Field(ge=0)
    lifecycle_event_count: int = Field(ge=0)
    events: tuple[EvidenceLifecycleEvent, ...]
    payload_sha256: str

    @model_validator(mode="before")
    @classmethod
    def validate_payload_digest(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        observed = payload.pop("payload_sha256", None)
        if observed != tombstone_payload_sha256(payload):
            raise ValueError("tombstone payload digest mismatch")
        return value

    @model_validator(mode="after")
    def validate_integrity(self) -> "TombstoneJournal":
        if self.lifecycle_event_count != len(self.events):
            raise ValueError("tombstone lifecycle_event_count mismatch")
        ordered = sorted(self.events, key=lambda item: (str(item.evidence_id), item.resulting_version))
        if list(self.events) != ordered:
            raise ValueError("tombstone events must use canonical ordering")
        seen: set[tuple[str, int]] = set()
        for event in self.events:
            key = (str(event.evidence_id), event.resulting_version)
            if key in seen:
                raise ValueError("duplicate tombstone lifecycle version")
            seen.add(key)
            if event.action is EvidenceLifecycleAction.REGISTER:
                raise ValueError("registration events are not privacy tombstones")
        return self


class LegalHold(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    hold_id: str
    backup_id: str
    reason: str
    created_at: datetime
    expires_at: datetime
    review_due_at: datetime

    @field_validator("hold_id", "backup_id", "reason")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("legal hold fields must not be blank")
        return value

    @model_validator(mode="after")
    def validate_window(self) -> "LegalHold":
        if self.expires_at <= self.created_at:
            raise ValueError("legal hold expiry must follow creation")
        if not self.created_at <= self.review_due_at <= self.expires_at:
            raise ValueError("legal hold review must occur within the hold window")
        return self


class BackupPrivacyPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True)

    schema_: str = Field(default="sentinel-edge-backup-privacy/1.0", alias="schema")
    backup_id: str
    retention_expires_at: datetime
    privacy_classes: tuple[str, ...] = ("internal", "restricted")
    secret_reference_policy: str = "references_only_no_secret_values"
    tombstone_journal_file: str = "privacy-tombstones.json"
    tombstone_journal_sha256: str
    tombstone_authority_position: int = Field(ge=0)
    legal_hold: LegalHold | None = None

    @model_validator(mode="after")
    def validate_policy(self) -> "BackupPrivacyPolicy":
        allowed = {"public", "internal", "restricted"}
        if not self.privacy_classes or set(self.privacy_classes) - allowed:
            raise ValueError("backup privacy classes are invalid")
        if self.legal_hold is not None and self.legal_hold.backup_id != self.backup_id:
            raise ValueError("legal hold must be scoped to the exact backup")
        return self


class BackupRetentionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    backup_id: str
    evaluated_at: datetime
    removable: bool
    active_legal_hold: bool
    retention_expired: bool
    reason_codes: tuple[str, ...]


def tombstone_payload_sha256(payload: dict[str, Any]) -> str:
    stable = {
        "schema": payload.get("schema", "sentinel-edge-privacy-tombstones/1.0"),
        "source_authority_position": int(payload.get("source_authority_position", 0)),
        "lifecycle_event_count": int(payload.get("lifecycle_event_count", len(payload.get("events", [])))),
        "events": payload.get("events", []),
    }
    return sha256_bytes(canonical_json_bytes(stable))


def build_tombstone_journal(store: Any, *, generated_at: datetime | None = None) -> TombstoneJournal:
    generated_at = generated_at or datetime.now(timezone.utc)
    events = tuple(sorted(
        (item for item in store.evidence_lifecycle_events() if item.action is not EvidenceLifecycleAction.REGISTER),
        key=lambda item: (str(item.evidence_id), item.resulting_version),
    ))
    authority = store.authority_conformance()
    seed = {
        "source_authority_position": int(authority["highest_contiguous_position"]),
        "event_ids": [str(item.lifecycle_event_id) for item in events],
    }
    journal_id = uuid5(NAMESPACE_URL, f"sentinel-privacy-tombstones:{sha256_bytes(canonical_json_bytes(seed))}")
    base = {
        "schema": "sentinel-edge-privacy-tombstones/1.0",
        "journal_id": str(journal_id),
        "generated_at": generated_at.isoformat(),
        "source_authority_position": int(authority["highest_contiguous_position"]),
        "lifecycle_event_count": len(events),
        "events": [item.model_dump(mode="json") for item in events],
    }
    return TombstoneJournal.model_validate({**base, "payload_sha256": tombstone_payload_sha256(base)})


def write_tombstone_journal(store: Any, output: str | Path, *, generated_at: datetime | None = None) -> TombstoneJournal:
    journal = build_tombstone_journal(store, generated_at=generated_at)
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(journal.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return journal


def load_tombstone_journal(path: str | Path) -> TombstoneJournal:
    return TombstoneJournal.model_validate(json.loads(Path(path).read_text(encoding="utf-8")))


def apply_tombstone_journal(store: Any, journal: TombstoneJournal) -> dict[str, int | str]:
    applied = 0
    skipped = 0
    for event in journal.events:
        try:
            current = store.evidence_lifecycle_projection(str(event.evidence_id))
        except KeyError as exc:
            raise ValueError(f"tombstone target evidence is missing: {event.evidence_id}") from exc
        if current.version >= event.resulting_version:
            skipped += 1
            continue
        if current.version != event.expected_version:
            raise ValueError(
                f"tombstone lifecycle gap for {event.evidence_id}: current={current.version} expected={event.expected_version}"
            )
        store.record_evidence_lifecycle(event)
        applied += 1
    return {
        "journal_id": str(journal.journal_id),
        "journal_sha256": journal.payload_sha256,
        "journal_authority_position": journal.source_authority_position,
        "applied": applied,
        "skipped": skipped,
    }


def retention_decision(policy: BackupPrivacyPolicy, *, now: datetime | None = None) -> BackupRetentionDecision:
    now = now or datetime.now(timezone.utc)
    retention_expired = now >= policy.retention_expires_at
    active_hold = bool(policy.legal_hold and policy.legal_hold.created_at <= now < policy.legal_hold.expires_at)
    reasons: list[str] = []
    if not retention_expired:
        reasons.append("retention_window_active")
    if active_hold:
        reasons.append("exact_backup_legal_hold_active")
    if retention_expired and not active_hold:
        reasons.append("retention_expired_no_active_hold")
    return BackupRetentionDecision(
        backup_id=policy.backup_id,
        evaluated_at=now,
        removable=retention_expired and not active_hold,
        active_legal_hold=active_hold,
        retention_expired=retention_expired,
        reason_codes=tuple(reasons),
    )
