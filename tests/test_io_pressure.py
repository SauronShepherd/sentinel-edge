from sentinel_edge.qualification.io_pressure import IoPressureSnapshot


def test_io_snapshot_distinguishes_io_stall_from_cpu_memory() -> None:
    snapshot = IoPressureSnapshot(0.8, 1.2, 0.2, 0.3, 0.4, 0.1, 0.2)
    assert snapshot.classify() == "io_stall_pressure"
    assert snapshot.as_snapshot()["fsync_tail_seconds"] == 0.2


def test_unavailable_io_metrics_are_explicit() -> None:
    assert IoPressureSnapshot(None, None, None, None, None, 0.4, 0.3).classify() == "io_metrics_unavailable"
