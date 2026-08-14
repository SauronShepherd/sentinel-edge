from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from uuid import NAMESPACE_URL, uuid5

from pydantic import BaseModel, ConfigDict, Field

from sentinel_edge.domain.models import Observation
from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file


class ObservationContractReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    valid: bool
    schema_name: str = "sentinel-edge-observation"
    schema_version: str
    observation_sha256: str
    reason_codes: tuple[str, ...] = ()


def validate_observation_contract(observation: Observation) -> ObservationContractReport:
    """Validate the single internal observation boundary used by every adapter."""
    normalized = observation.model_dump(mode="json")
    reasons: list[str] = []
    if observation.schema_version != "2.0.0":
        reasons.append("unsupported_observation_schema_version")
    if not observation.values or set(observation.values) != set(observation.units):
        reasons.append("observation_values_units_mismatch")
    return ObservationContractReport(
        valid=not reasons,
        schema_version=observation.schema_version,
        observation_sha256=sha256_bytes(canonical_json_bytes(normalized)),
        reason_codes=tuple(sorted(reasons or ["observation_contract_valid"])),
    )


class MigrationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_name: str
    from_version: str
    to_version: str
    state: str
    raw_payload_sha256: str
    normalized_payload_sha256: str | None = None
    raw_payload: dict[str, Any]
    normalized_payload: dict[str, Any] | None = None
    reason_codes: tuple[str, ...] = ()


class DatabaseMigrationRehearsal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_sha256_before: str
    source_sha256_after: str
    copy_integrity_before: str
    copy_integrity_after: str
    migration_applied: bool
    rollback_restore_verified: bool
    active_store_unchanged: bool
    reason_codes: tuple[str, ...]


class ContractHandshake(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    component_id: str
    schema_versions: dict[str, str]
    supported_peer_versions: dict[str, tuple[str, ...]]

    def compatible_with(self, peer: "ContractHandshake") -> tuple[bool, tuple[str, ...]]:
        reasons: list[str] = []
        for schema, version in self.schema_versions.items():
            peer_supported = peer.supported_peer_versions.get(schema, ())
            if version not in peer_supported:
                reasons.append(f"peer_rejects:{schema}:{version}")
        for schema, version in peer.schema_versions.items():
            local_supported = self.supported_peer_versions.get(schema, ())
            if version not in local_supported:
                reasons.append(f"local_rejects:{schema}:{version}")
        return not reasons, tuple(sorted(reasons or ["contracts_compatible"]))


@dataclass(frozen=True)
class LegacyObservationPolicy:
    source_id: str
    allowed_properties: frozenset[str]
    property_aliases: dict[str, str]
    allowed_units: dict[str, frozenset[str]]


class ObservationMigrator:
    """Exact source-specific V1 -> V2 migration with raw-payload preservation."""

    def __init__(self, policies: tuple[LegacyObservationPolicy, ...]) -> None:
        self._policies = {item.source_id: item for item in policies}

    def migrate(self, payload: dict[str, Any]) -> MigrationResult:
        raw = json.loads(json.dumps(payload))
        raw_digest = sha256_bytes(canonical_json_bytes(raw))
        version = str(payload.get("schema_version", "1.0.0"))
        if version == "2.0.0":
            normalized = Observation.model_validate(payload).model_dump(mode="json")
            return MigrationResult(
                schema_name="sentinel-edge-observation",
                from_version=version,
                to_version="2.0.0",
                state="unchanged",
                raw_payload_sha256=raw_digest,
                normalized_payload_sha256=sha256_bytes(canonical_json_bytes(normalized)),
                raw_payload=raw,
                normalized_payload=normalized,
                reason_codes=("already_current",),
            )
        if version != "1.0.0":
            return MigrationResult(
                schema_name="sentinel-edge-observation",
                from_version=version,
                to_version="2.0.0",
                state="quarantined",
                raw_payload_sha256=raw_digest,
                raw_payload=raw,
                reason_codes=("unsupported_source_schema",),
            )
        source_id = str(payload.get("source_id", ""))
        policy = self._policies.get(source_id)
        if policy is None:
            return MigrationResult(
                schema_name="sentinel-edge-observation",
                from_version=version,
                to_version="2.0.0",
                state="quarantined",
                raw_payload_sha256=raw_digest,
                raw_payload=raw,
                reason_codes=("source_specific_migration_missing",),
            )
        values = payload.get("values")
        units = payload.get("units")
        if not isinstance(values, dict) or not isinstance(units, dict) or set(values) != set(units):
            return MigrationResult(
                schema_name="sentinel-edge-observation",
                from_version=version,
                to_version="2.0.0",
                state="quarantined",
                raw_payload_sha256=raw_digest,
                raw_payload=raw,
                reason_codes=("ambiguous_parallel_value_unit_contract",),
            )
        normalized_values: dict[str, float] = {}
        normalized_units: dict[str, str] = {}
        reasons: list[str] = []
        for source_key, value in values.items():
            target = policy.property_aliases.get(source_key, source_key)
            if target not in policy.allowed_properties:
                reasons.append(f"property_not_allowed:{source_key}")
                continue
            if target in normalized_values:
                reasons.append(f"alias_collision:{target}")
                continue
            unit = str(units[source_key])
            if unit not in policy.allowed_units.get(target, frozenset()):
                reasons.append(f"unit_not_allowed:{target}:{unit}")
                continue
            normalized_values[target] = float(value)
            normalized_units[target] = unit
        if reasons:
            return MigrationResult(
                schema_name="sentinel-edge-observation",
                from_version=version,
                to_version="2.0.0",
                state="quarantined",
                raw_payload_sha256=raw_digest,
                raw_payload=raw,
                reason_codes=tuple(sorted(reasons)),
            )
        candidate = {**payload, "schema_version": "2.0.0", "values": normalized_values, "units": normalized_units}
        candidate.setdefault("observation_id", str(uuid5(NAMESPACE_URL, f"sentinel-migrated-observation:{raw_digest}")))
        candidate.setdefault("correlation_id", str(uuid5(NAMESPACE_URL, f"sentinel-migrated-correlation:{source_id}:{payload.get('sequence', 0)}:{raw_digest}")))
        normalized = Observation.model_validate(candidate).model_dump(mode="json")
        return MigrationResult(
            schema_name="sentinel-edge-observation",
            from_version=version,
            to_version="2.0.0",
            state="migrated",
            raw_payload_sha256=raw_digest,
            normalized_payload_sha256=sha256_bytes(canonical_json_bytes(normalized)),
            raw_payload=raw,
            normalized_payload=normalized,
            reason_codes=("exact_source_specific_migration", "raw_payload_preserved"),
        )


def rehearse_sqlite_migration(
    source: str | Path,
    migration: Callable[[sqlite3.Connection], None],
) -> DatabaseMigrationRehearsal:
    source_path = Path(source)
    before = sha256_file(source_path)
    reasons: list[str] = []
    migration_applied = False
    rollback_verified = False
    with tempfile.TemporaryDirectory(prefix="sentinel-migration-") as tmp:
        copy_path = Path(tmp) / source_path.name
        shutil.copy2(source_path, copy_path)
        connection = sqlite3.connect(copy_path)
        integrity_before = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
        try:
            connection.execute("BEGIN IMMEDIATE")
            migration(connection)
            connection.commit()
            migration_applied = True
        except Exception as exc:
            connection.rollback()
            reasons.append(f"migration_failed:{type(exc).__name__}")
        integrity_after = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
        connection.close()
        restore_path = Path(tmp) / "restore.sqlite3"
        shutil.copy2(source_path, restore_path)
        rollback_verified = sha256_file(restore_path) == before
    after = sha256_file(source_path)
    unchanged = before == after
    if integrity_before != "ok":
        reasons.append("copy_integrity_failed_before")
    if integrity_after != "ok":
        reasons.append("copy_integrity_failed_after")
    if not unchanged:
        reasons.append("active_store_changed")
    if rollback_verified:
        reasons.append("rollback_restore_verified")
    return DatabaseMigrationRehearsal(
        source_sha256_before=before,
        source_sha256_after=after,
        copy_integrity_before=integrity_before,
        copy_integrity_after=integrity_after,
        migration_applied=migration_applied,
        rollback_restore_verified=rollback_verified,
        active_store_unchanged=unchanged,
        reason_codes=tuple(sorted(set(reasons))),
    )
