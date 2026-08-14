from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from uuid import NAMESPACE_URL, uuid5

from sentinel_edge.authority import AuthorityWatermark
from sentinel_edge.privacy import (
    BackupPrivacyPolicy,
    LegalHold,
    TombstoneJournal,
    apply_tombstone_journal,
    build_tombstone_journal,
    load_tombstone_journal,
    retention_decision,
)
from sentinel_edge.security import canonical_json_bytes, sha256_bytes
from sentinel_edge.storage.sqlite_store import ConfigurationStore, IncidentJournalStore, SourceCursorStore
from sentinel_edge.storage.restore_authorization import RestoreAuthorization


_MODULE_FILES = {
    "collector": "collector.sqlite3",
    "incidents": "incidents.sqlite3",
    "configuration": "configuration.sqlite3",
    "critical_spool": "critical-spool.sqlite3",
    "disposition": "disposition.sqlite3",
    "secret_metadata": "secret-metadata.sqlite3",
    "key_lifecycle": "key-lifecycle.sqlite3",
    "audit_checkpoints": "audit-checkpoints.sqlite3",
}
_MANIFEST_FILE = "backup-manifest.json"
_TOMBSTONE_FILE = "privacy-tombstones.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _integrity(path: Path) -> str:
    connection = sqlite3.connect(path)
    try:
        return str(connection.execute("PRAGMA integrity_check").fetchone()[0])
    finally:
        connection.close()


def _table_counts(path: Path) -> dict[str, int]:
    connection = sqlite3.connect(path)
    try:
        tables = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()]
        return {table: int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]) for table in tables}
    finally:
        connection.close()


def _online_backup(source: Path, destination: Path) -> None:
    source_connection = sqlite3.connect(source)
    destination_connection = sqlite3.connect(destination)
    try:
        source_connection.backup(destination_connection)
        destination_connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        destination_connection.commit()
    finally:
        destination_connection.close()
        source_connection.close()


class StateBackupManager:
    """Per-module online checkpoints with explicit privacy/tombstone closure.

    The backup remains a per-module checkpoint. It never claims a globally atomic
    snapshot. A newer tombstone journal can be supplied during restore and is
    applied before the restored directory is exposed.
    """

    schema = "sentinel-edge-state-backup/1.2"

    def create(
        self,
        state_dir: str | Path,
        output_zip: str | Path,
        *,
        retention_days: int = 30,
        legal_hold_id: str | None = None,
        legal_hold_reason: str | None = None,
        legal_hold_expires_at: datetime | None = None,
        legal_hold_review_due_at: datetime | None = None,
        created_at: datetime | None = None,
    ) -> Path:
        if retention_days <= 0:
            raise ValueError("backup retention_days must be positive")
        hold_fields = (legal_hold_id, legal_hold_reason, legal_hold_expires_at, legal_hold_review_due_at)
        if any(value is not None for value in hold_fields) and not all(value is not None for value in hold_fields):
            raise ValueError("legal hold requires id, reason, expiry, and review due time")
        state_dir = Path(state_dir)
        output_zip = Path(output_zip)
        output_zip.parent.mkdir(parents=True, exist_ok=True)
        created_at = created_at or datetime.now(timezone.utc)
        with tempfile.TemporaryDirectory(prefix="sentinel-backup-") as temp_name:
            temp = Path(temp_name)
            modules: dict[str, dict[str, object]] = {}
            for module, filename in _MODULE_FILES.items():
                source = state_dir / filename
                if not source.is_file():
                    continue
                destination = temp / filename
                _online_backup(source, destination)
                integrity = _integrity(destination)
                if integrity != "ok":
                    raise RuntimeError(f"backup integrity failed for {module}: {integrity}")
                modules[module] = {
                    "file": filename,
                    "bytes": destination.stat().st_size,
                    "sha256": _sha256(destination),
                    "integrity_check": integrity,
                    "table_counts": _table_counts(destination),
                }
            required = {"collector", "incidents", "configuration"}
            if not required <= modules.keys():
                raise FileNotFoundError(f"state directory lacks required modules: {sorted(required - modules.keys())}")

            try:
                incident_store = IncidentJournalStore(temp / _MODULE_FILES["incidents"])
                tombstones = build_tombstone_journal(incident_store, generated_at=created_at)
                (temp / _TOMBSTONE_FILE).write_text(
                    json.dumps(tombstones.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )

                authority_watermark = AuthorityWatermark.from_conformance(incident_store.authority_conformance())
                if not authority_watermark.valid:
                    raise RuntimeError("cannot back up a non-conformant authority journal")
                incident_connection = sqlite3.connect(temp / _MODULE_FILES["incidents"])
                collector_connection = sqlite3.connect(temp / _MODULE_FILES["collector"])
                authority_position = authority_watermark.highest_contiguous_position
                incident_versions = int(incident_connection.execute(
                    "SELECT COUNT(*) FROM incident_events"
                ).fetchone()[0])
                source_watermarks = {
                    row[0]: {
                        "boot_id": row[1], "clock_epoch": row[2], "last_sequence": row[3],
                        "event_time_watermark": row[4],
                    }
                    for row in collector_connection.execute(
                        "SELECT source_id,boot_id,clock_epoch,last_sequence,last_observed_at FROM source_cursors ORDER BY source_id"
                    ).fetchall()
                }
            finally:
                incident_connection.close()
                collector_connection.close()
                incident_store.close()

            backup_id = str(uuid5(NAMESPACE_URL, json.dumps({
                "created_at": created_at.isoformat(),
                "modules": {key: value["sha256"] for key, value in sorted(modules.items())},
                "tombstones": tombstones.payload_sha256,
            }, sort_keys=True)))
            hold = None
            if legal_hold_id is not None:
                assert legal_hold_reason is not None and legal_hold_expires_at is not None and legal_hold_review_due_at is not None
                hold = LegalHold(
                    hold_id=legal_hold_id,
                    backup_id=backup_id,
                    reason=legal_hold_reason,
                    created_at=created_at,
                    expires_at=legal_hold_expires_at,
                    review_due_at=legal_hold_review_due_at,
                )
            privacy = BackupPrivacyPolicy(
                backup_id=backup_id,
                retention_expires_at=created_at + timedelta(days=retention_days),
                tombstone_journal_sha256=tombstones.payload_sha256,
                tombstone_authority_position=tombstones.source_authority_position,
                legal_hold=hold,
            )
            manifest = {
                "schema": self.schema,
                "backup_id": backup_id,
                "created_at": created_at.isoformat(),
                "consistency": "per_module_online_checkpoint",
                "global_atomic_snapshot_claimed": False,
                "restore_requires_projection_rebuild": True,
                "modules": modules,
                "authority_watermark": authority_watermark.model_dump(mode="json"),
                "watermarks": {
                    "incident_authority_position": authority_position,
                    "incident_event_count": incident_versions,
                    "source_cursors": source_watermarks,
                },
                "privacy": privacy.model_dump(mode="json"),
            }
            (temp / _MANIFEST_FILE).write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            fd, temp_zip_name = tempfile.mkstemp(prefix=".tmp-backup-", suffix=".zip", dir=output_zip.parent)
            os.close(fd)
            try:
                with zipfile.ZipFile(temp_zip_name, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                    archive.write(temp / _MANIFEST_FILE, _MANIFEST_FILE)
                    archive.write(temp / _TOMBSTONE_FILE, _TOMBSTONE_FILE)
                    for record in modules.values():
                        archive.write(temp / str(record["file"]), str(record["file"]))
                os.replace(temp_zip_name, output_zip)
            finally:
                if os.path.exists(temp_zip_name):
                    os.unlink(temp_zip_name)
        return output_zip

    def verify(self, backup_zip: str | Path) -> dict[str, object]:
        backup_zip = Path(backup_zip)
        errors: list[str] = []
        with tempfile.TemporaryDirectory(prefix="sentinel-verify-backup-") as temp_name:
            temp = Path(temp_name)
            with zipfile.ZipFile(backup_zip) as archive:
                names = archive.namelist()
                if len(names) != len(set(names)):
                    errors.append("duplicate_archive_member")
                for name in names:
                    path = PurePosixPath(name)
                    if path.is_absolute() or ".." in path.parts:
                        errors.append(f"unsafe_member:{name}")
                if errors:
                    return {"valid": False, "errors": sorted(errors)}
                archive.extractall(temp)
            manifest_path = temp / _MANIFEST_FILE
            if not manifest_path.is_file():
                return {"valid": False, "errors": ["manifest_missing"]}
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("schema") != self.schema:
                errors.append("schema_mismatch")
            if manifest.get("global_atomic_snapshot_claimed") is not False:
                errors.append("unsupported_global_atomicity_claim")
            declared = {_MANIFEST_FILE, _TOMBSTONE_FILE}
            for module, record in manifest.get("modules", {}).items():
                declared.add(str(record["file"]))
                path = temp / record["file"]
                if not path.is_file():
                    errors.append(f"module_missing:{module}")
                    continue
                if path.stat().st_size != record["bytes"]:
                    errors.append(f"size_mismatch:{module}")
                if _sha256(path) != record["sha256"]:
                    errors.append(f"digest_mismatch:{module}")
                if _integrity(path) != "ok":
                    errors.append(f"integrity_failed:{module}")
                if _table_counts(path) != record["table_counts"]:
                    errors.append(f"table_count_mismatch:{module}")
            actual = {path.name for path in temp.iterdir() if path.is_file()}
            if actual != declared:
                errors.append("archive_member_closure_failed")

            incidents_path = temp / _MODULE_FILES["incidents"]
            if incidents_path.is_file():
                authority_store = IncidentJournalStore(incidents_path)
                try:
                    actual_authority = AuthorityWatermark.from_conformance(authority_store.authority_conformance())
                    declared_authority = AuthorityWatermark.model_validate(manifest["authority_watermark"])
                    if declared_authority != actual_authority:
                        errors.append("authority_watermark_not_bound_to_incident_store")
                except (KeyError, ValueError) as exc:
                    errors.append(f"authority_watermark_invalid:{exc}")
                finally:
                    authority_store.close()

            privacy = None
            journal = None
            try:
                privacy = BackupPrivacyPolicy.model_validate(manifest["privacy"])
            except (KeyError, ValueError) as exc:
                errors.append(f"privacy_policy_invalid:{exc}")
            journal_path = temp / _TOMBSTONE_FILE
            if not journal_path.is_file():
                errors.append("tombstone_journal_missing")
            else:
                try:
                    journal = load_tombstone_journal(journal_path)
                except ValueError as exc:
                    errors.append(f"tombstone_journal_invalid:{exc}")
            if privacy is not None and journal is not None:
                if privacy.backup_id != manifest.get("backup_id"):
                    errors.append("privacy_backup_id_mismatch")
                if privacy.tombstone_journal_sha256 != journal.payload_sha256:
                    errors.append("tombstone_journal_digest_mismatch")
                if privacy.tombstone_authority_position != journal.source_authority_position:
                    errors.append("tombstone_authority_position_mismatch")
                if journal.source_authority_position > int(manifest.get("watermarks", {}).get("incident_authority_position", -1)):
                    errors.append("tombstone_watermark_exceeds_authority")
                if incidents_path.is_file():
                    store = IncidentJournalStore(incidents_path)
                    try:
                        stored = tuple(
                            item for item in store.evidence_lifecycle_events()
                            if item.action.value != "register"
                        )
                        if tuple(journal.events) != tuple(sorted(stored, key=lambda item: (str(item.evidence_id), item.resulting_version))):
                            errors.append("tombstone_journal_not_closed_over_incident_store")
                    finally:
                        store.close()
            return {
                "valid": not errors,
                "errors": sorted(errors),
                "backup_id": manifest.get("backup_id"),
                "manifest": manifest,
                "privacy": privacy.model_dump(mode="json") if privacy else None,
                "tombstone_journal": journal.model_dump(mode="json") if journal else None,
            }

    def retention_decision(self, backup_zip: str | Path, *, now: datetime | None = None) -> dict[str, object]:
        verification = self.verify(backup_zip)
        if not verification["valid"]:
            raise ValueError(f"backup verification failed: {verification['errors']}")
        policy = BackupPrivacyPolicy.model_validate(verification["privacy"])
        return retention_decision(policy, now=now).model_dump(mode="json")

    def delete_if_expired(
        self,
        backup_zip: str | Path,
        *,
        now: datetime | None = None,
        actor: str,
        receipt_path: str | Path | None = None,
    ) -> dict[str, object]:
        if not actor.strip():
            raise ValueError("backup deletion actor must not be blank")
        backup_zip = Path(backup_zip)
        decision = self.retention_decision(backup_zip, now=now)
        if not decision["removable"]:
            raise PermissionError(f"backup is not removable: {decision['reason_codes']}")
        backup_sha256 = _sha256(backup_zip)
        bytes_removed = backup_zip.stat().st_size
        backup_zip.unlink()
        evaluated_at = str(decision["evaluated_at"])
        payload = {
            "schema": "sentinel-edge-backup-deletion/1.0",
            "backup_id": decision["backup_id"],
            "backup_sha256": backup_sha256,
            "bytes_removed": bytes_removed,
            "actor": actor,
            "deleted_at": evaluated_at,
            "reason_codes": decision["reason_codes"],
        }
        receipt = {**payload, "receipt_sha256": sha256_bytes(canonical_json_bytes(payload))}
        if receipt_path is not None:
            Path(receipt_path).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return receipt

    def restore(
        self,
        backup_zip: str | Path,
        target_dir: str | Path,
        *,
        replace: bool = False,
        current_tombstone_journal: str | Path | TombstoneJournal | None = None,
        authorization: RestoreAuthorization | None = None,
        target_node: str = "local-node",
        target_namespace: str | None = None,
    ) -> dict[str, object]:
        if authorization is None:
            raise PermissionError("explicit restore authorization is required")
        authorization.validate(expected_node=target_node, expected_namespace=target_namespace or target_dir.name)
        verification = self.verify(backup_zip)
        if not verification["valid"]:
            raise ValueError(f"backup verification failed: {verification['errors']}")
        target_dir = Path(target_dir)
        if target_dir.exists() and any(target_dir.iterdir()) and not replace:
            raise FileExistsError("target restore directory is not empty")
        parent = target_dir.parent
        parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{target_dir.name}.restore-", dir=parent))
        try:
            with zipfile.ZipFile(backup_zip) as archive:
                archive.extractall(staging)
            manifest = verification["manifest"]
            (staging / ".restore-required.json").write_text(
                json.dumps({"backup_id": manifest["backup_id"], "required": True}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            collector = SourceCursorStore(staging / _MODULE_FILES["collector"])
            incidents = IncidentJournalStore(staging / _MODULE_FILES["incidents"])
            configuration = ConfigurationStore(staging / _MODULE_FILES["configuration"])

            bundled = TombstoneJournal.model_validate(verification["tombstone_journal"])
            bundled_result = apply_tombstone_journal(incidents, bundled)
            current_result = None
            if current_tombstone_journal is not None:
                current = (
                    current_tombstone_journal
                    if isinstance(current_tombstone_journal, TombstoneJournal)
                    else load_tombstone_journal(current_tombstone_journal)
                )
                if current.source_authority_position < bundled.source_authority_position:
                    raise ValueError("current tombstone journal is older than the backup journal")
                current_result = apply_tombstone_journal(incidents, current)
                (staging / _TOMBSTONE_FILE).write_text(
                    json.dumps(current.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )

            source_count = len(collector.load_all())
            from sentinel_edge.incidents.engine import IncidentEventEngine
            engine = IncidentEventEngine(incidents)
            incident_count = len(engine.journal())
            active_configuration = configuration.active() is not None
            expected_incidents = int(manifest["watermarks"]["incident_event_count"])
            if incident_count != expected_incidents:
                raise RuntimeError("restored incident event count differs from backup watermark")
            if not active_configuration:
                raise RuntimeError("restored configuration has no active bundle")
            authority = incidents.authority_conformance()
            if not authority["valid"]:
                raise RuntimeError("restored authority journal is invalid after tombstone application")
            reconciliation = {
                "backup_id": manifest["backup_id"],
                "reconciled_at": datetime.now(timezone.utc).isoformat(),
                "source_count": source_count,
                "incident_event_count": incident_count,
                "projection_count": len(engine.current()),
                "active_configuration": active_configuration,
                "bundled_tombstones": bundled_result,
                "current_tombstones": current_result,
                "tombstones_applied_before_readiness": True,
                "authority_watermark": AuthorityWatermark.from_conformance(authority).model_dump(mode="json"),
                "authority_highest_contiguous_position": authority["highest_contiguous_position"],
                "credentials_rebound": False,
                "credential_recovery_required": True,
                "ready_for_startup": True,
            }
            (staging / ".restore-reconciled.json").write_text(
                json.dumps(reconciliation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            (staging / ".restore-required.json").unlink()
            collector.close()
            incidents.close()
            configuration.close()
            if target_dir.exists():
                shutil.rmtree(target_dir)
            # Windows can briefly retain a handle after SQLite connections are
            # closed (notably under pytest's temp-directory cleanup). Retry the
            # atomic directory replacement without weakening the rollback path.
            replace_error = None
            for attempt in range(20):
                try:
                    os.replace(staging, target_dir)
                    replace_error = None
                    break
                except PermissionError as exc:
                    replace_error = exc
                    if attempt == 19:
                        raise
                    time.sleep(0.05)
            if replace_error is not None:
                raise replace_error
            return reconciliation
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise
