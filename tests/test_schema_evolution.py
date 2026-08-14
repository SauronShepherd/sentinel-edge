import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from sentinel_edge.evolution import (
    ContractHandshake,
    LegacyObservationPolicy,
    ObservationMigrator,
    rehearse_sqlite_migration,
)
from sentinel_edge.security import sha256_file


def policy() -> LegacyObservationPolicy:
    return LegacyObservationPolicy(
        source_id="legacy-gauge-1",
        allowed_properties=frozenset({"water_level_m", "rate_of_rise_m_per_h"}),
        property_aliases={"level": "water_level_m", "rise": "rate_of_rise_m_per_h"},
        allowed_units={"water_level_m": frozenset({"m"}), "rate_of_rise_m_per_h": frozenset({"m/h"})},
    )


def legacy_payload() -> dict:
    now = datetime(2026, 8, 2, 18, 0, tzinfo=timezone.utc).isoformat()
    return {
        "schema_version": "1.0.0",
        "source_id": "legacy-gauge-1",
        "hazard": "flood",
        "source_mode": "fixture",
        "sequence": 1,
        "observed_at": now,
        "received_at": now,
        "values": {"level": 1.2, "rise": 0.3},
        "units": {"level": "m", "rise": "m/h"},
    }


def test_exact_source_specific_observation_migration_preserves_raw_payload() -> None:
    report = ObservationMigrator((policy(),)).migrate(legacy_payload())
    assert report.state == "migrated"
    assert report.raw_payload["values"] == {"level": 1.2, "rise": 0.3}
    assert report.normalized_payload["schema_version"] == "2.0.0"
    assert report.normalized_payload["values"] == {"rate_of_rise_m_per_h": 0.3, "water_level_m": 1.2}
    assert report.raw_payload_sha256 != report.normalized_payload_sha256
    assert "raw_payload_preserved" in report.reason_codes


def test_ambiguous_or_unregistered_legacy_input_is_quarantined() -> None:
    migrator = ObservationMigrator((policy(),))
    unknown = legacy_payload() | {"source_id": "unknown"}
    assert migrator.migrate(unknown).state == "quarantined"
    broken = legacy_payload()
    broken["units"] = {"level": "m"}
    result = migrator.migrate(broken)
    assert result.state == "quarantined"
    assert "ambiguous_parallel_value_unit_contract" in result.reason_codes


def test_contract_handshake_blocks_mixed_incompatible_workers() -> None:
    collector = ContractHandshake(
        component_id="collector",
        schema_versions={"observation": "2.0.0"},
        supported_peer_versions={"analysis": ("1.0.0",), "observation": ("2.0.0",)},
    )
    analysis = ContractHandshake(
        component_id="analysis",
        schema_versions={"analysis": "2.0.0"},
        supported_peer_versions={"observation": ("1.0.0",)},
    )
    compatible, reasons = collector.compatible_with(analysis)
    assert compatible is False
    assert any("rejects" in item for item in reasons)


def test_database_migration_runs_on_copy_and_preserves_active_store(tmp_path: Path) -> None:
    path = tmp_path / "active.sqlite3"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE example(id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
    connection.execute("INSERT INTO example(value) VALUES ('before')")
    connection.commit()
    connection.close()
    before = sha256_file(path)

    def migration(copy: sqlite3.Connection) -> None:
        copy.execute("ALTER TABLE example ADD COLUMN version INTEGER NOT NULL DEFAULT 1")

    report = rehearse_sqlite_migration(path, migration)
    assert report.migration_applied is True
    assert report.copy_integrity_before == "ok"
    assert report.copy_integrity_after == "ok"
    assert report.active_store_unchanged is True
    assert report.rollback_restore_verified is True
    assert sha256_file(path) == before
