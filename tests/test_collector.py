from datetime import datetime, timedelta, timezone
import pytest

from sentinel_edge.collector import BoundedRingBuffer, StreamingSourceCollector
from sentinel_edge.domain.models import HazardKind, Observation, SourceMode


def observation(sequence: int) -> Observation:
    now = datetime.now(timezone.utc) + timedelta(milliseconds=sequence)
    return Observation(source_id="imu", hazard=HazardKind.EARTHQUAKE, source_mode=SourceMode.FIXTURE,
                       sequence=sequence, observed_at=now, received_at=now,
                       values={"accel_x":0.0}, units={"accel_x":"g"})


def test_ring_buffer_is_bounded() -> None:
    buffer = BoundedRingBuffer(2)
    for sequence in range(3): buffer.append(observation(sequence))
    assert len(buffer.snapshot()) == 2
    assert buffer.dropped == 1


def test_source_kind_and_location_are_configurable_and_immutable() -> None:
    collector = StreamingSourceCollector()
    config = collector.configure_source("cam", source_kind="rtsp", location="rtsp://camera.local/live")
    assert config.source_kind == "rtsp"
    assert collector.source_configurations() == (config,)
    with pytest.raises(ValueError, match="immutable"):
        collector.configure_source("cam", source_kind="video_fixture", location="fixtures/camera.jsonl")


def test_collector_rejects_replayed_sequence() -> None:
    collector = StreamingSourceCollector()
    collector.ingest(observation(1))
    with pytest.raises(ValueError, match="sequence"):
        collector.ingest(observation(1))


def test_collector_rejects_replayed_mode_before_it_can_become_a_live_event() -> None:
    collector = StreamingSourceCollector()
    replay = observation(99).model_copy(update={"source_mode": SourceMode.REPLAYED})
    with pytest.raises(ValueError, match="replayed observations"):
        collector.ingest(replay)
    assert collector.health() == ()


def test_adapter_lateness_is_bounded_and_audited() -> None:
    collector = StreamingSourceCollector()
    collector.configure_source("imu", source_kind="imu", location="local", max_lateness_seconds=1.0)
    first = observation(1)
    collector.ingest(first)
    late = first.model_copy(update={"sequence": 2, "observed_at": first.observed_at - timedelta(milliseconds=500), "received_at": first.received_at + timedelta(milliseconds=500)})
    collector.ingest(late)
    health = collector.health()[0]
    assert "late_event" in health.reason_codes
    assert health.event_time_watermark == first.observed_at

    too_late = first.model_copy(update={"sequence": 3, "observed_at": first.observed_at - timedelta(seconds=2), "received_at": first.received_at + timedelta(seconds=2)})
    with pytest.raises(ValueError, match="lateness bound"):
        collector.ingest(too_late)
    assert "late_event_exceeded" in collector.health()[0].reason_codes
