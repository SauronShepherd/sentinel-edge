from datetime import datetime, timedelta, timezone
from pathlib import Path

from sentinel_edge.runtime import MaintenanceAction, MaintenanceCoordinator, MaintenanceDisposition
from sentinel_edge.storage import ContentAddressedArtifactStore, TelemetryBatchWriter


def test_high_rate_telemetry_is_batched_and_reports_write_budget(tmp_path: Path) -> None:
    store = ContentAddressedArtifactStore(tmp_path / "artifacts", max_bytes=4 * 1024 * 1024, reserve_bytes=64 * 1024)
    writer = TelemetryBatchWriter(
        store,
        batch_items=100,
        flush_interval_seconds=60,
        bytes_per_day_budget=2 * 1024 * 1024 * 1024,
        retention_days=7,
    )
    start = datetime(2026, 8, 2, 0, 0, tzinfo=timezone.utc)
    for index in range(1000):
        writer.append(
            {"source": "imu", "sequence": index, "x": index / 1000.0},
            observed_at=start + timedelta(milliseconds=10 * index),
        )
    writer.flush()
    report = writer.report()
    assert report.observations == 1000
    assert report.batches == 10
    assert len(writer.artifact_refs) == 10
    assert report.write_amplification_proxy <= 1.10
    assert report.within_budget is True
    assert report.retention_days == 7


def test_maintenance_is_deferred_or_forced_around_tier_a_windows() -> None:
    coordinator = MaintenanceCoordinator()
    deferred = coordinator.decide(
        MaintenanceAction.WAL_CHECKPOINT,
        tier_a_protected_window=True,
    )
    assert deferred.disposition is MaintenanceDisposition.DEFERRED
    assert "tier_a_protected_window" in deferred.reason_codes
    assert deferred.expected_service_consequence == "none_expected"

    forced = coordinator.decide(
        MaintenanceAction.ARTIFACT_GC,
        tier_a_protected_window=True,
        storage_pressure=True,
    )
    assert forced.disposition is MaintenanceDisposition.FORCED
    assert "maintenance_forced" in forced.reason_codes
    assert "latency" in forced.expected_service_consequence
    assert len(coordinator.history()) == 2
