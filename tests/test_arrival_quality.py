from sentinel_edge.benchmark.arrival_quality import ArrivalQualityReport


def test_arrival_jitter_and_overhead_within_envelope_is_qualified() -> None:
    report = ArrivalQualityReport(0.010, 0.005, 0.02, 0.05)
    assert report.valid is True
    assert report.label() == "qualified"


def test_jitter_or_overhead_beyond_envelope_invalidates_block() -> None:
    report = ArrivalQualityReport(0.010, 0.020, 0.02, 0.05)
    assert report.valid is False
    assert report.label() == "invalidated_or_labeled"
