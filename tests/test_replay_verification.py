import pytest

from sentinel_edge.qualification import ReplayCheckClass, verify_replay


def test_byte_exact_replay_reports_class_and_passes() -> None:
    report = verify_replay({"state": "confirmed"}, {"state": "confirmed"}, check_class=ReplayCheckClass.BYTE_EXACT)
    assert report.passed is True
    assert report.check_class is ReplayCheckClass.BYTE_EXACT
    assert report.absolute_tolerance == 0.0
    assert report.mismatch_paths == ()


def test_numeric_tolerance_replay_reports_tolerance_and_mismatch() -> None:
    passed = verify_replay({"score": 0.5}, {"score": 0.5005}, check_class=ReplayCheckClass.NUMERIC_TOLERANCE, absolute_tolerance=0.001)
    failed = verify_replay({"score": 0.5}, {"score": 0.51}, check_class=ReplayCheckClass.NUMERIC_TOLERANCE, absolute_tolerance=0.001)
    assert passed.passed is True
    assert passed.absolute_tolerance == 0.001
    assert failed.passed is False
    assert failed.mismatch_paths == ("score",)


def test_semantic_replay_checks_declared_fields_only() -> None:
    report = verify_replay(
        {"state": "confirmed", "latency_ms": 10},
        {"state": "confirmed", "latency_ms": 999},
        check_class=ReplayCheckClass.SEMANTIC,
        semantic_fields=("state",),
    )
    assert report.passed is True
    assert report.semantic_fields == ("state",)
    with pytest.raises(ValueError, match="semantic_fields"):
        verify_replay({}, {}, check_class=ReplayCheckClass.SEMANTIC)
