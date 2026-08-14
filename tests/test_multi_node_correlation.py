from datetime import datetime, timedelta, timezone

from sentinel_edge.qualification import NodeSignal, correlate_simulated_nodes


def test_simulated_multi_node_correlation_shows_clock_offsets() -> None:
    start = datetime(2026, 8, 12, 12, 30, tzinfo=timezone.utc)
    report = correlate_simulated_nodes((
        NodeSignal(node_id="node-a", observed_at=start, signal_score=0.8, clock_offset_ms=0.0),
        NodeSignal(node_id="node-b", observed_at=start + timedelta(milliseconds=120), signal_score=0.7, clock_offset_ms=37.5),
        NodeSignal(node_id="node-c", observed_at=start + timedelta(milliseconds=240), signal_score=0.6, clock_offset_ms=-12.0),
    ))
    assert report.correlated is True
    assert report.node_count == 3
    assert report.clock_offsets_shown is True
    assert {node.clock_offset_ms for node in report.nodes} == {0.0, 37.5, -12.0}
    assert report.classification == "simulated"


def test_correlation_window_rejects_separated_nodes() -> None:
    start = datetime(2026, 8, 12, 12, 30, tzinfo=timezone.utc)
    report = correlate_simulated_nodes((
        NodeSignal(node_id="node-a", observed_at=start, signal_score=0.8),
        NodeSignal(node_id="node-b", observed_at=start + timedelta(seconds=2), signal_score=0.7),
    ), correlation_window_ms=500)
    assert report.correlated is False
