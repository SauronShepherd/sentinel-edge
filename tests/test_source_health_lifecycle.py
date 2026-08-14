from datetime import datetime, timedelta, timezone
from pathlib import Path

from sentinel_edge.collector import StreamingSourceCollector
from sentinel_edge.domain.models import HazardKind, HealthState, Observation, SourceMode
from sentinel_edge.storage import SourceCursorStore


def observation(sequence: int, at: datetime, *, boot_id: str = "boot-a") -> Observation:
    return Observation(
        source_id="source-health",
        hazard=HazardKind.FLOOD,
        source_mode=SourceMode.FIXTURE,
        boot_id=boot_id,
        sequence=sequence,
        observed_at=at,
        received_at=at,
        values={"water_level_m": 0.2},
        units={"water_level_m": "m"},
    )


def test_source_timeout_failure_and_recovery_are_durable_audit_events(tmp_path: Path) -> None:
    path = tmp_path / "source.sqlite3"
    start = datetime(2026, 8, 2, 10, 0, tzinfo=timezone.utc)
    collector = StreamingSourceCollector(cursor_store=SourceCursorStore(path))
    collector.ingest(observation(1, start))
    collector.mark_stale(start + timedelta(minutes=1), threshold_seconds=30)
    collector.mark_failed("source-health", "transport_lost", start + timedelta(minutes=2))
    collector.ingest(observation(2, start + timedelta(minutes=3)))

    assert collector.health()[0].state is HealthState.HEALTHY
    assert "source_recovered" in collector.health()[0].reason_codes
    events = collector.health_events()
    assert [item.state for item in events] == [
        HealthState.HEALTHY,
        HealthState.STALE,
        HealthState.FAILED,
        HealthState.HEALTHY,
    ]
    assert events[-1].previous_state is HealthState.FAILED

    restarted = StreamingSourceCollector(cursor_store=SourceCursorStore(path))
    assert restarted.health()[0].state is HealthState.HEALTHY
    assert len(restarted.health_events()) == 4
