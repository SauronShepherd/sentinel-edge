from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4
import zipfile

import pytest

from sentinel_edge.domain.models import AnalysisResult, CoverageState, HazardKind, IncidentState
from sentinel_edge.scenario import DeterministicScenarioEngine, load_scenario
from sentinel_edge.storage import (
    ArtifactPolicy,
    ContentAddressedArtifactStore,
    CriticalAnalysisSpool,
    IncidentJournalStore,
    SpoolExhaustedError,
    StateBackupManager,
)
from sentinel_edge.storage.restore_authorization import RestoreAuthorization


def analysis(index: int = 1) -> AnalysisResult:
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc) + timedelta(seconds=index)
    return AnalysisResult(
        analysis_id=uuid4(),
        observation_id=uuid4(),
        correlation_id=uuid4(),
        boot_id="boot-a",
        hazard=HazardKind.EARTHQUAKE,
        score=0.8,
        state_hint=IncidentState.SUSPECTED,
        features={"peak_g": 0.2},
        coverage=CoverageState.SUFFICIENT,
        produced_at=now,
    )


def test_critical_spool_is_bounded_idempotent_and_never_silently_overwrites(tmp_path: Path) -> None:
    spool = CriticalAnalysisSpool(tmp_path / "spool.sqlite3", max_items=1, max_bytes=100_000, max_age_seconds=60)
    item = analysis(1)
    assert spool.enqueue(item, enqueued_at=item.produced_at) is True
    assert spool.enqueue(item, enqueued_at=item.produced_at) is False
    with pytest.raises(SpoolExhaustedError, match="exhausted"):
        spool.enqueue(analysis(2), enqueued_at=item.produced_at)
    assert len(spool.pending()) == 1
    assert any(event["status"] == "rejected" for event in spool.events())


def test_expired_critical_spool_item_remains_visible_and_pending(tmp_path: Path) -> None:
    spool = CriticalAnalysisSpool(tmp_path / "spool.sqlite3", max_age_seconds=1)
    item = analysis(1)
    spool.enqueue(item, enqueued_at=item.produced_at)
    delivered = spool.drain(lambda _: None, now=item.produced_at + timedelta(seconds=2))
    assert delivered == ()
    assert len(spool.pending()) == 1
    assert spool.metrics(now=item.produced_at + timedelta(seconds=2)).expired_items == 1
    assert any(event["status"] == "expired" for event in spool.events())


def test_scenario_engine_spools_during_authority_outage_and_reconciles_in_order(tmp_path: Path) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    scenario = load_scenario("fixtures/scenarios/simultaneous-event.json")
    raw = scenario["observations"][0]
    from sentinel_edge.domain.models import Observation
    observation = Observation.model_validate(raw)
    result = engine.analysis.analyze(observation)
    engine.set_incident_authority_available(False, reason="simulated_outage")
    assert engine.apply_or_spool(result, observation.received_at) is None
    assert engine.critical_spool.metrics(now=observation.received_at).pending_items == 1
    delivered = engine.recover_incident_authority(now=observation.received_at)
    assert delivered == (str(result.analysis_id),)
    assert engine.critical_spool.metrics(now=observation.received_at).pending_items == 0
    assert len(engine.incidents.journal()) == 1


def test_artifact_store_preserves_critical_reserve_and_reports_read_only_degradation(tmp_path: Path) -> None:
    store = ContentAddressedArtifactStore(tmp_path / "artifacts", max_bytes=32, reserve_bytes=8)
    store.put_bytes(b"a" * 23, policy=ArtifactPolicy.internal_operational())
    with pytest.raises(OSError, match="reserve"):
        store.put_bytes(b"bb", policy=ArtifactPolicy.internal_operational())
    critical = store.put_bytes(b"bb", critical=True, policy=ArtifactPolicy.incident_evidence())
    assert store.verify(critical)
    assert store.usage_report()["critical_budget_remaining_bytes"] == 7
    store.set_read_only(True)
    assert store.health().writable is False
    with pytest.raises(OSError, match="read-only"):
        store.put_bytes(b"critical", critical=True, policy=ArtifactPolicy.incident_evidence())


def test_incident_store_uses_full_wal_durability_and_reports_checkpoint(tmp_path: Path) -> None:
    store = IncidentJournalStore(tmp_path / "incidents.sqlite3")
    profile = store.durability_profile()
    assert profile["journal_mode"] == "wal"
    assert profile["critical_truth_full_durability"] is True
    assert store.integrity_check() == "ok"
    checkpoint = store.checkpoint("PASSIVE")
    assert checkpoint["mode"] == "PASSIVE"
    assert checkpoint["duration_ms"] >= 0


def test_state_backup_is_per_module_verified_and_restores_reconciled_state(tmp_path: Path) -> None:
    source = tmp_path / "source"
    engine = DeterministicScenarioEngine(state_dir=source)
    result = engine.run(load_scenario("fixtures/scenarios/simultaneous-event.json"))
    assert result.incident_versions == 4

    backup = tmp_path / "sentinel-backup.zip"
    manager = StateBackupManager()
    manager.create(source, backup)
    verification = manager.verify(backup)
    assert verification["valid"] is True
    assert verification["manifest"]["global_atomic_snapshot_claimed"] is False
    assert verification["manifest"]["consistency"] == "per_module_online_checkpoint"

    restored = tmp_path / "restored"
    reconciliation = manager.restore(backup, restored, authorization=RestoreAuthorization(
        actor="operator", reason="recovery", target_node="local-node", target_namespace="restored", policy_version="restore-v1"))
    assert reconciliation["ready_for_startup"] is True
    assert reconciliation["credential_recovery_required"] is True
    assert reconciliation["credentials_rebound"] is False
    assert reconciliation["incident_event_count"] == 4
    assert (restored / ".restore-reconciled.json").is_file()
    assert not (restored / ".restore-required.json").exists()
    restarted = DeterministicScenarioEngine(state_dir=restored)
    assert restarted.readiness.state.value == "ready"
    assert len(restarted.incidents.journal()) == 4


def test_backup_tampering_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "source"
    engine = DeterministicScenarioEngine(state_dir=source)
    engine.run(load_scenario("fixtures/scenarios/simultaneous-event.json"))
    backup = tmp_path / "backup.zip"
    manager = StateBackupManager()
    manager.create(source, backup)

    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(backup) as original, zipfile.ZipFile(tampered, "w") as output:
        for name in original.namelist():
            data = original.read(name)
            if name == "incidents.sqlite3":
                data += b"tamper"
            output.writestr(name, data)
    verification = manager.verify(tampered)
    assert verification["valid"] is False
    assert any("mismatch:incidents" in error for error in verification["errors"])


def test_read_only_evidence_medium_enters_visible_degraded_storage_without_stopping_monitoring(tmp_path: Path) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    engine.set_storage_read_only(True)
    result = engine.run(load_scenario("fixtures/scenarios/simultaneous-event.json"))
    assert result.final_states["earthquake"] == "confirmed"
    evidence = next(item for item in engine.capabilities.records() if item.capability_id == "evidence")
    assert evidence.state.value == "degraded"
    assert "degraded_storage_read_only" in evidence.reason_codes
    assert result.storage["writable"] is False
