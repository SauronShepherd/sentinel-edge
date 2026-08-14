from datetime import datetime, timezone

from sentinel_edge.collector import StreamingSourceCollector
from sentinel_edge.domain.models import HazardKind, Observation, SourceMode
from sentinel_edge.storage import SourceCursorStore


def observation(sequence: int, uncertainty: float, *, clock_epoch: int = 0) -> Observation:
    now = datetime(2026, 8, 12, 10, 0, tzinfo=timezone.utc)
    return Observation(
        source_id="imu-clock", hazard=HazardKind.EARTHQUAKE, source_mode=SourceMode.LIVE,
        boot_id="boot-a", sequence=sequence, observed_at=now, received_at=now,
        clock_epoch=clock_epoch, clock_uncertainty_ms=uncertainty,
        values={"accel_x": 0.1}, units={"accel_x": "g"},
    )


def test_clock_uncertainty_is_retained_in_health_and_restart(tmp_path) -> None:
    path = tmp_path / "cursor.sqlite3"
    collector = StreamingSourceCollector(cursor_store=SourceCursorStore(path))
    collector.ingest(observation(1, 12.5))
    assert collector.health()[0].clock_uncertainty_ms == 12.5
    restarted = StreamingSourceCollector(cursor_store=SourceCursorStore(path))
    assert restarted.health()[0].clock_uncertainty_ms == 12.5


def test_gap_and_epoch_transition_remain_explicit_with_clock_metadata(tmp_path) -> None:
    collector = StreamingSourceCollector(cursor_store=SourceCursorStore(tmp_path / "cursor.sqlite3"))
    collector.ingest(observation(1, 2.0))
    collector.ingest(observation(3, 4.0))
    assert "sequence_gap" in collector.health()[0].reason_codes
    collector.ingest(observation(1, 7.0, clock_epoch=1))
    assert "source_epoch_transition" in collector.health()[0].reason_codes
    assert collector.health()[0].clock_uncertainty_ms == 7.0
