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

from sentinel_edge.security import canonical_json_bytes, sha256_bytes


class ArtifactClassification(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    SECRET_PROHIBITED = "secret_prohibited"


class ArtifactRetention(StrEnum):
    EPHEMERAL = "ephemeral"
    OPERATIONAL = "operational"
    INCIDENT_EVIDENCE = "incident_evidence"
    RELEASE_PROOF = "release_proof"
    LEGAL_HOLD = "legal_hold"


class ArtifactEncryption(StrEnum):
    NONE = "none"
    NODE_AT_REST = "node_at_rest"
    EXTERNAL_ENVELOPE_REQUIRED = "external_envelope_required"


class ArtifactExportPolicy(StrEnum):
    ALLOWED = "allowed"
    REDACTED_ONLY = "redacted_only"
    PROHIBITED = "prohibited"


class ArtifactDeletionPolicy(StrEnum):
    GC_ALLOWED = "gc_allowed"
    TOMBSTONE_REQUIRED = "tombstone_required"
    HOLD_PROTECTED = "hold_protected"
    MANUAL_ONLY = "manual_only"


class ArtifactReferenceKind(StrEnum):
    LEASE = "lease"
    LEGAL_HOLD = "legal_hold"
    INCIDENT_HOLD = "incident_hold"
    RELEASE_CANDIDATE = "release_candidate"
    TARGET_BINDING = "target_binding"
    MINIMUM_PROOF = "minimum_proof"


class ArtifactReadDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    allowed: bool
    disclose_digest: bool
    reason_codes: tuple[str, ...]


def authorize_artifact_read(
    policy: "ArtifactPolicy",
    *,
    owner: str,
    requester: str,
    verification_role: bool,
    integrity_valid: bool,
    observed_bytes: int,
    max_bytes: int,
) -> ArtifactReadDecision:
    """Authorize a read only after owner, integrity, and size checks."""
    reasons: list[str] = []
    if not owner.strip() or requester != owner:
        reasons.append("wrong_owner")
    if not integrity_valid:
        reasons.append("integrity_failed")
    if observed_bytes < 0 or max_bytes <= 0 or observed_bytes > max_bytes:
        reasons.append("oversize")
    if policy.classification is ArtifactClassification.RESTRICTED and not verification_role:
        reasons.append("restricted_read_unauthorized")
    allowed = not reasons
    return ArtifactReadDecision(
        allowed=allowed,
        disclose_digest=allowed and (policy.classification is not ArtifactClassification.RESTRICTED or verification_role),
        reason_codes=tuple(reasons) or ("artifact_read_authorized",),
    )


_CLASS_ORDER = {
    ArtifactClassification.PUBLIC: 0,
    ArtifactClassification.INTERNAL: 1,
    ArtifactClassification.RESTRICTED: 2,
    ArtifactClassification.SECRET_PROHIBITED: 3,
}


class ArtifactPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    classification: ArtifactClassification
    retention: ArtifactRetention
    encryption: ArtifactEncryption
    export_policy: ArtifactExportPolicy
    deletion_policy: ArtifactDeletionPolicy
    retention_expires_at: datetime | None = None
    reason_codes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_policy(self) -> "ArtifactPolicy":
        if self.classification is ArtifactClassification.SECRET_PROHIBITED:
            raise ValueError("secret-prohibited artifact persistence is forbidden")
        if self.classification is ArtifactClassification.RESTRICTED and self.export_policy is ArtifactExportPolicy.ALLOWED:
            raise ValueError("restricted artifacts require redacted-only or prohibited export policy")
        if self.retention is ArtifactRetention.LEGAL_HOLD and self.deletion_policy is not ArtifactDeletionPolicy.HOLD_PROTECTED:
            raise ValueError("legal-hold artifacts must be hold protected")
        if self.retention_expires_at is not None and self.retention is ArtifactRetention.LEGAL_HOLD:
            # Hold review/expiry is managed by an explicit reference, not by silently aging the object.
            raise ValueError("legal-hold retention expiry must be represented by an explicit hold reference")
        return self

    @classmethod
    def internal_operational(cls) -> "ArtifactPolicy":
        return cls(
            classification=ArtifactClassification.INTERNAL,
            retention=ArtifactRetention.OPERATIONAL,
            encryption=ArtifactEncryption.NODE_AT_REST,
            export_policy=ArtifactExportPolicy.ALLOWED,
            deletion_policy=ArtifactDeletionPolicy.GC_ALLOWED,
            reason_codes=("default_internal_operational",),
        )

    @classmethod
    def incident_evidence(cls, *, restricted: bool = True) -> "ArtifactPolicy":
        return cls(
            classification=ArtifactClassification.RESTRICTED if restricted else ArtifactClassification.INTERNAL,
            retention=ArtifactRetention.INCIDENT_EVIDENCE,
            encryption=ArtifactEncryption.NODE_AT_REST,
            export_policy=ArtifactExportPolicy.REDACTED_ONLY if restricted else ArtifactExportPolicy.ALLOWED,
            deletion_policy=ArtifactDeletionPolicy.TOMBSTONE_REQUIRED,
            reason_codes=("incident_evidence",),
        )


    @classmethod
    def configuration_bundle(cls) -> "ArtifactPolicy":
        return cls(
            classification=ArtifactClassification.INTERNAL,
            retention=ArtifactRetention.OPERATIONAL,
            encryption=ArtifactEncryption.NODE_AT_REST,
            export_policy=ArtifactExportPolicy.PROHIBITED,
            deletion_policy=ArtifactDeletionPolicy.MANUAL_ONLY,
            reason_codes=("configuration_bundle",),
        )

    @classmethod
    def telemetry_batch(cls) -> "ArtifactPolicy":
        return cls(
            classification=ArtifactClassification.INTERNAL,
            retention=ArtifactRetention.EPHEMERAL,
            encryption=ArtifactEncryption.NODE_AT_REST,
            export_policy=ArtifactExportPolicy.PROHIBITED,
            deletion_policy=ArtifactDeletionPolicy.GC_ALLOWED,
            reason_codes=("noncritical_telemetry",),
        )

    @classmethod
    def after_event_review(cls) -> "ArtifactPolicy":
        return cls(
            classification=ArtifactClassification.RESTRICTED,
            retention=ArtifactRetention.INCIDENT_EVIDENCE,
            encryption=ArtifactEncryption.NODE_AT_REST,
            export_policy=ArtifactExportPolicy.REDACTED_ONLY,
            deletion_policy=ArtifactDeletionPolicy.TOMBSTONE_REQUIRED,
            reason_codes=("after_event_review",),
        )

    @classmethod
    def claim_registry(cls) -> "ArtifactPolicy":
        return cls(
            classification=ArtifactClassification.INTERNAL,
            retention=ArtifactRetention.RELEASE_PROOF,
            encryption=ArtifactEncryption.NODE_AT_REST,
            export_policy=ArtifactExportPolicy.REDACTED_ONLY,
            deletion_policy=ArtifactDeletionPolicy.HOLD_PROTECTED,
            reason_codes=("claim_registry",),
        )

    @classmethod
    def sanitized_media(cls) -> "ArtifactPolicy":
        return cls(
            classification=ArtifactClassification.RESTRICTED,
            retention=ArtifactRetention.INCIDENT_EVIDENCE,
            encryption=ArtifactEncryption.NODE_AT_REST,
            export_policy=ArtifactExportPolicy.REDACTED_ONLY,
            deletion_policy=ArtifactDeletionPolicy.TOMBSTONE_REQUIRED,
            reason_codes=("sanitized_untrusted_media",),
        )

    @classmethod
    def export_bundle(cls, *, public: bool) -> "ArtifactPolicy":
        if public:
            return cls.release_proof()
        return cls(
            classification=ArtifactClassification.INTERNAL,
            retention=ArtifactRetention.OPERATIONAL,
            encryption=ArtifactEncryption.NODE_AT_REST,
            export_policy=ArtifactExportPolicy.ALLOWED,
            deletion_policy=ArtifactDeletionPolicy.MANUAL_ONLY,
            reason_codes=("governed_internal_export",),
        )
    @classmethod
    def release_proof(cls) -> "ArtifactPolicy":
        return cls(
            classification=ArtifactClassification.PUBLIC,
            retention=ArtifactRetention.RELEASE_PROOF,
            encryption=ArtifactEncryption.NONE,
            export_policy=ArtifactExportPolicy.ALLOWED,
            deletion_policy=ArtifactDeletionPolicy.HOLD_PROTECTED,
            reason_codes=("release_proof",),
        )


class ArtifactScope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str | None = None
    incident_id: str | None = None
    scenario_run_id: str | None = None
    release_candidate_id: str | None = None

    @field_validator("source_id", "incident_id", "scenario_run_id", "release_candidate_id")
    @classmethod
    def normalize_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("artifact scope values must not be blank")
        return value


class ArtifactBudgetPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    node_max_objects: int = Field(default=100_000, ge=1)
    per_source_max_objects: int = Field(default=10_000, ge=1)
    per_source_max_bytes: int = Field(default=128 * 1024 * 1024, ge=1)
    per_incident_max_objects: int = Field(default=10_000, ge=1)
    per_incident_max_bytes: int = Field(default=256 * 1024 * 1024, ge=1)
    per_run_max_objects: int = Field(default=20_000, ge=1)
    per_run_max_bytes: int = Field(default=512 * 1024 * 1024, ge=1)
    per_candidate_max_objects: int = Field(default=20_000, ge=1)
    per_candidate_max_bytes: int = Field(default=512 * 1024 * 1024, ge=1)


class ArtifactRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    registration_id: UUID
    sha256: str
    relative_path: str
    bytes: int = Field(ge=0)
    media_type: str
    policy: ArtifactPolicy
    scope: ArtifactScope
    critical: bool
    created_at: datetime
    policy_sha256: str


class ArtifactReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    reference_id: UUID
    artifact_sha256: str
    kind: ArtifactReferenceKind
    owner: str
    reason: str
    created_at: datetime
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def validate_reference(self) -> "ArtifactReference":
        if not self.owner.strip() or not self.reason.strip():
            raise ValueError("artifact reference owner and reason are required")
        if self.expires_at is not None and self.expires_at <= self.created_at:
            raise ValueError("artifact reference expiry must follow creation")
        return self


class ArtifactCatalog:
    """SQLite catalog for artifact policy, scope budgets, references and GC decisions."""

    def __init__(self, path: str | Path, *, budgets: ArtifactBudgetPolicy | None = None) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.budgets = budgets or ArtifactBudgetPolicy()
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=FULL")
        self._connection.execute("PRAGMA busy_timeout=5000")
        self._connection.row_factory = sqlite3.Row
        self._lock = RLock()
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS artifact_registrations (
                registration_id TEXT PRIMARY KEY,
                sha256 TEXT NOT NULL,
                relative_path TEXT NOT NULL,
                bytes INTEGER NOT NULL,
                media_type TEXT NOT NULL,
                classification TEXT NOT NULL,
                policy_sha256 TEXT NOT NULL,
                policy_json TEXT NOT NULL,
                scope_json TEXT NOT NULL,
                source_id TEXT,
                incident_id TEXT,
                scenario_run_id TEXT,
                release_candidate_id TEXT,
                critical INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_artifact_registrations_sha ON artifact_registrations(sha256);
            CREATE INDEX IF NOT EXISTS idx_artifact_registrations_source ON artifact_registrations(source_id);
            CREATE INDEX IF NOT EXISTS idx_artifact_registrations_incident ON artifact_registrations(incident_id);
            CREATE INDEX IF NOT EXISTS idx_artifact_registrations_run ON artifact_registrations(scenario_run_id);
            CREATE INDEX IF NOT EXISTS idx_artifact_registrations_candidate ON artifact_registrations(release_candidate_id);
            CREATE TABLE IF NOT EXISTS artifact_references (
                reference_id TEXT PRIMARY KEY,
                artifact_sha256 TEXT NOT NULL,
                kind TEXT NOT NULL,
                owner TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                payload_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_artifact_references_sha ON artifact_references(artifact_sha256);
            CREATE TABLE IF NOT EXISTS artifact_gc_events (
                event_id TEXT PRIMARY KEY,
                artifact_sha256 TEXT NOT NULL,
                action TEXT NOT NULL,
                actor TEXT NOT NULL,
                reason_codes_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            """
        )

    @staticmethod
    def _policy_digest(policy: ArtifactPolicy) -> str:
        return sha256_bytes(canonical_json_bytes(policy.model_dump(mode="json")))

    def _scope_usage(self, field: str, value: str) -> tuple[int, int]:
        row = self._connection.execute(
            f"SELECT COUNT(*) AS objects, COALESCE(SUM(bytes),0) AS bytes FROM artifact_registrations WHERE {field}=?",
            (value,),
        ).fetchone()
        return int(row["objects"]), int(row["bytes"])

    def _check_scope_budget(self, scope: ArtifactScope, size: int) -> None:
        total = self._connection.execute("SELECT COUNT(*) AS count FROM artifact_registrations").fetchone()
        if int(total["count"]) + 1 > self.budgets.node_max_objects:
            raise OSError("artifact node object-count budget exceeded")
        checks = (
            ("source_id", scope.source_id, self.budgets.per_source_max_objects, self.budgets.per_source_max_bytes),
            ("incident_id", scope.incident_id, self.budgets.per_incident_max_objects, self.budgets.per_incident_max_bytes),
            ("scenario_run_id", scope.scenario_run_id, self.budgets.per_run_max_objects, self.budgets.per_run_max_bytes),
            ("release_candidate_id", scope.release_candidate_id, self.budgets.per_candidate_max_objects, self.budgets.per_candidate_max_bytes),
        )
        for field, value, max_objects, max_bytes in checks:
            if value is None:
                continue
            objects, used = self._scope_usage(field, value)
            if objects + 1 > max_objects:
                raise OSError(f"artifact {field} object-count budget exceeded")
            if used + size > max_bytes:
                raise OSError(f"artifact {field} byte budget exceeded")

    def register(
        self,
        *,
        sha256: str,
        relative_path: str,
        bytes_count: int,
        media_type: str,
        policy: ArtifactPolicy,
        scope: ArtifactScope,
        critical: bool,
        created_at: datetime | None = None,
    ) -> ArtifactRecord:
        created_at = created_at or datetime.now(timezone.utc)
        policy_sha256 = self._policy_digest(policy)
        registration_id = uuid5(
            NAMESPACE_URL,
            "sentinel-artifact-registration:"
            + sha256_bytes(canonical_json_bytes({
                "sha256": sha256,
                "policy_sha256": policy_sha256,
                "scope": scope.model_dump(mode="json"),
                "critical": critical,
            })),
        )
        record = ArtifactRecord(
            registration_id=registration_id,
            sha256=sha256,
            relative_path=relative_path,
            bytes=bytes_count,
            media_type=media_type,
            policy=policy,
            scope=scope,
            critical=critical,
            created_at=created_at,
            policy_sha256=policy_sha256,
        )
        with self._lock, self._connection:
            existing = self._connection.execute(
                "SELECT policy_sha256,scope_json FROM artifact_registrations WHERE registration_id=?",
                (str(registration_id),),
            ).fetchone()
            if existing is not None:
                if existing["policy_sha256"] != policy_sha256 or json.loads(existing["scope_json"]) != scope.model_dump(mode="json"):
                    raise ValueError("artifact registration identity conflict")
                return record
            self._check_scope_budget(scope, bytes_count)
            self._connection.execute(
                """INSERT INTO artifact_registrations(
                   registration_id,sha256,relative_path,bytes,media_type,classification,policy_sha256,policy_json,
                   scope_json,source_id,incident_id,scenario_run_id,release_candidate_id,critical,created_at
                   ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    str(registration_id), sha256, relative_path, bytes_count, media_type, policy.classification.value,
                    policy_sha256, policy.model_dump_json(), scope.model_dump_json(), scope.source_id, scope.incident_id,
                    scope.scenario_run_id, scope.release_candidate_id, int(critical), created_at.isoformat(),
                ),
            )
        return record

    def records(self, sha256: str | None = None) -> tuple[ArtifactRecord, ...]:
        if sha256 is None:
            rows = self._connection.execute(
                "SELECT * FROM artifact_registrations ORDER BY created_at,registration_id"
            ).fetchall()
        else:
            rows = self._connection.execute(
                "SELECT * FROM artifact_registrations WHERE sha256=? ORDER BY created_at,registration_id",
                (sha256,),
            ).fetchall()
        return tuple(
            ArtifactRecord(
                registration_id=UUID(row["registration_id"]),
                sha256=row["sha256"],
                relative_path=row["relative_path"],
                bytes=int(row["bytes"]),
                media_type=row["media_type"],
                policy=ArtifactPolicy.model_validate(json.loads(row["policy_json"])),
                scope=ArtifactScope.model_validate(json.loads(row["scope_json"])),
                critical=bool(row["critical"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                policy_sha256=row["policy_sha256"],
            )
            for row in rows
        )

    def effective_policy(self, sha256: str) -> ArtifactPolicy:
        records = self.records(sha256)
        if not records:
            raise KeyError(sha256)
        most_restrictive = max(records, key=lambda item: _CLASS_ORDER[item.policy.classification]).policy
        export_policy = (
            ArtifactExportPolicy.PROHIBITED
            if any(item.policy.export_policy is ArtifactExportPolicy.PROHIBITED for item in records)
            else ArtifactExportPolicy.REDACTED_ONLY
            if any(item.policy.export_policy is ArtifactExportPolicy.REDACTED_ONLY for item in records)
            else ArtifactExportPolicy.ALLOWED
        )
        deletion_policy = (
            ArtifactDeletionPolicy.HOLD_PROTECTED
            if any(item.policy.deletion_policy is ArtifactDeletionPolicy.HOLD_PROTECTED for item in records)
            else ArtifactDeletionPolicy.TOMBSTONE_REQUIRED
            if any(item.policy.deletion_policy is ArtifactDeletionPolicy.TOMBSTONE_REQUIRED for item in records)
            else ArtifactDeletionPolicy.MANUAL_ONLY
            if any(item.policy.deletion_policy is ArtifactDeletionPolicy.MANUAL_ONLY for item in records)
            else ArtifactDeletionPolicy.GC_ALLOWED
        )
        encryption = (
            ArtifactEncryption.EXTERNAL_ENVELOPE_REQUIRED
            if any(item.policy.encryption is ArtifactEncryption.EXTERNAL_ENVELOPE_REQUIRED for item in records)
            else ArtifactEncryption.NODE_AT_REST
            if any(item.policy.encryption is ArtifactEncryption.NODE_AT_REST for item in records)
            else ArtifactEncryption.NONE
        )
        retention = max(records, key=lambda item: list(ArtifactRetention).index(item.policy.retention)).policy.retention
        expiries = [item.policy.retention_expires_at for item in records if item.policy.retention_expires_at is not None]
        return ArtifactPolicy(
            classification=most_restrictive.classification,
            retention=retention,
            encryption=encryption,
            export_policy=export_policy,
            deletion_policy=deletion_policy,
            retention_expires_at=min(expiries) if expiries else None,
            reason_codes=tuple(sorted({code for item in records for code in item.policy.reason_codes})),
        )

    def add_reference(
        self,
        artifact_sha256: str,
        *,
        kind: ArtifactReferenceKind,
        owner: str,
        reason: str,
        expires_at: datetime | None = None,
        created_at: datetime | None = None,
    ) -> ArtifactReference:
        if not self.records(artifact_sha256):
            raise KeyError(artifact_sha256)
        created_at = created_at or datetime.now(timezone.utc)
        reference_id = uuid5(
            NAMESPACE_URL,
            f"sentinel-artifact-reference:{artifact_sha256}:{kind.value}:{owner}:{reason}:{expires_at.isoformat() if expires_at else ''}",
        )
        ref = ArtifactReference(
            reference_id=reference_id,
            artifact_sha256=artifact_sha256,
            kind=kind,
            owner=owner,
            reason=reason,
            created_at=created_at,
            expires_at=expires_at,
        )
        with self._lock, self._connection:
            row = self._connection.execute(
                "SELECT payload_json FROM artifact_references WHERE reference_id=?", (str(reference_id),)
            ).fetchone()
            if row is not None:
                return ArtifactReference.model_validate(json.loads(row["payload_json"]))
            self._connection.execute(
                """INSERT INTO artifact_references(
                   reference_id,artifact_sha256,kind,owner,reason,created_at,expires_at,payload_json
                   ) VALUES (?,?,?,?,?,?,?,?)""",
                (
                    str(reference_id), artifact_sha256, kind.value, owner, reason, created_at.isoformat(),
                    expires_at.isoformat() if expires_at else None, ref.model_dump_json(),
                ),
            )
        return ref

    def references(self, artifact_sha256: str, *, now: datetime | None = None) -> tuple[ArtifactReference, ...]:
        now = now or datetime.now(timezone.utc)
        rows = self._connection.execute(
            "SELECT payload_json FROM artifact_references WHERE artifact_sha256=? ORDER BY created_at,reference_id",
            (artifact_sha256,),
        ).fetchall()
        refs = tuple(ArtifactReference.model_validate(json.loads(row[0])) for row in rows)
        return tuple(item for item in refs if item.expires_at is None or item.expires_at > now)

    def remove_reference(self, reference_id: UUID | str) -> None:
        with self._lock, self._connection:
            self._connection.execute("DELETE FROM artifact_references WHERE reference_id=?", (str(reference_id),))

    def deletion_blockers(self, artifact_sha256: str, *, now: datetime | None = None) -> tuple[str, ...]:
        policy = self.effective_policy(artifact_sha256)
        blockers = [f"policy:{policy.deletion_policy.value}"] if policy.deletion_policy is not ArtifactDeletionPolicy.GC_ALLOWED else []
        blockers.extend(f"reference:{item.kind.value}:{item.reference_id}" for item in self.references(artifact_sha256, now=now))
        return tuple(sorted(blockers))

    def record_gc_event(self, artifact_sha256: str, *, action: str, actor: str, reason_codes: tuple[str, ...]) -> dict[str, Any]:
        created_at = datetime.now(timezone.utc)
        payload = {
            "artifact_sha256": artifact_sha256,
            "action": action,
            "actor": actor,
            "reason_codes": list(reason_codes),
            "created_at": created_at.isoformat(),
        }
        event_id = uuid5(NAMESPACE_URL, f"sentinel-artifact-gc:{sha256_bytes(canonical_json_bytes(payload))}")
        payload["event_id"] = str(event_id)
        with self._lock, self._connection:
            self._connection.execute(
                """INSERT OR IGNORE INTO artifact_gc_events(
                   event_id,artifact_sha256,action,actor,reason_codes_json,created_at,payload_json
                   ) VALUES (?,?,?,?,?,?,?)""",
                (
                    str(event_id), artifact_sha256, action, actor, json.dumps(list(reason_codes)),
                    created_at.isoformat(), json.dumps(payload, sort_keys=True),
                ),
            )
        return payload

    def usage(self) -> dict[str, Any]:
        row = self._connection.execute(
            "SELECT COUNT(*) AS registrations,COUNT(DISTINCT sha256) AS objects,COALESCE(SUM(bytes),0) AS logical_bytes FROM artifact_registrations"
        ).fetchone()
        by_class = {
            item["classification"]: {"registrations": int(item["count"]), "logical_bytes": int(item["bytes"])}
            for item in self._connection.execute(
                "SELECT classification,COUNT(*) AS count,COALESCE(SUM(bytes),0) AS bytes FROM artifact_registrations GROUP BY classification"
            ).fetchall()
        }
        return {
            "registrations": int(row["registrations"]),
            "objects": int(row["objects"]),
            "logical_bytes": int(row["logical_bytes"]),
            "by_classification": by_class,
            "budgets": self.budgets.model_dump(mode="json"),
        }

    def close(self) -> None:
        self._connection.close()
