from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from sentinel_edge.collector import StreamingSourceCollector
from sentinel_edge.domain.models import AnalysisResult, CoverageState, HazardKind, IncidentState, Observation, SourceMode
from sentinel_edge.incidents import IncidentEventEngine
from sentinel_edge.storage import IncidentJournalStore, SourceCursorStore


def obs(sequence: int, *, boot_id: str = "boot-a", observed_at: datetime | None = None) -> Observation:
    observed_at = observed_at or datetime(2026, 8, 2, 8, 0, tzinfo=timezone.utc)
    return Observation(
        source_id="imu-recovery",
        hazard=HazardKind.EARTHQUAKE,
        source_mode=SourceMode.FIXTURE,
        boot_id=boot_id,
        sequence=sequence,
        observed_at=observed_at,
        received_at=observed_at,
        values={"accel_x": 0.1},
        units={"accel_x": "g"},
    )


def test_durable_source_cursor_blocks_replay_and_allows_new_boot_sequence_reset(tmp_path) -> None:
    path = tmp_path / "collector.sqlite3"
    first = StreamingSourceCollector(cursor_store=SourceCursorStore(path))
    first.ingest(obs(7))
    restarted = StreamingSourceCollector(cursor_store=SourceCursorStore(path))
    with pytest.raises(ValueError, match="sequence"):
        restarted.ingest(obs(7))
    later = datetime(2026, 8, 2, 8, 0, 1, tzinfo=timezone.utc)
    accepted = restarted.ingest(obs(1, boot_id="boot-b", observed_at=later))
    assert accepted.sequence == 1
    assert "source_epoch_transition" in restarted.health()[0].reason_codes


def test_incident_engine_recovers_latest_state_and_deduplicates_analysis(tmp_path) -> None:
    path = tmp_path / "incidents.sqlite3"
    analysis_id = uuid4()
    analysis = AnalysisResult(
        analysis_id=analysis_id,
        observation_id=uuid4(),
        correlation_id=UUID("11111111-1111-1111-1111-111111111111"),
        boot_id="boot-a",
        hazard=HazardKind.WILDFIRE,
        score=0.8,
        state_hint=IncidentState.SUSPECTED,
        features={},
        coverage=CoverageState.SUFFICIENT,
    )
    first = IncidentEventEngine(IncidentJournalStore(path))
    first.apply_analysis(analysis)
    restarted = IncidentEventEngine(IncidentJournalStore(path))
    assert restarted.current()[0].state is IncidentState.SUSPECTED
    duplicate = restarted.apply_analysis(analysis)
    assert duplicate.version == 1
    assert len(restarted.journal()) == 1
