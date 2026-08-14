import pytest

from sentinel_edge.qualification import decompose_latency


def test_latency_report_decomposes_event_ingest_and_decision_times() -> None:
    report = decompose_latency("camera-1", {
        "capture_at": "2026-08-12T10:00:00+00:00",
        "ingest_at": "2026-08-12T10:00:00.120000+00:00",
        "decision_at": "2026-08-12T10:00:00.350000+00:00",
    })
    assert report.event_to_ingest_ms == 120.0
    assert report.ingest_to_decision_ms == 230.0
    assert report.event_to_decision_ms == 350.0


def test_latency_report_rejects_non_monotonic_chain() -> None:
    with pytest.raises(ValueError, match="monotonic"):
        decompose_latency("imu-1", {
            "capture_at": "2026-08-12T10:00:01+00:00",
            "ingest_at": "2026-08-12T10:00:00+00:00",
            "decision_at": "2026-08-12T10:00:02+00:00",
        })
