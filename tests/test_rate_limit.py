import pytest

from sentinel_edge.qualification.rate_limit import evaluate_rate_limit


def test_rate_limit_logs_reason_duration_workload_and_preserves_minimum_cadence() -> None:
    result = evaluate_rate_limit(reason="thermal load", duration_seconds=30, affected_workload="video",
        requested_cadence_seconds=10, minimum_local_cadence_seconds=60)
    assert result.suppressed is True
    assert result.effective_cadence_seconds == 60
    assert result.affected_workload == "video"


def test_rate_limit_rejects_invalid_duration() -> None:
    with pytest.raises(ValueError):
        evaluate_rate_limit(reason="x", duration_seconds=-1, affected_workload="x",
            requested_cadence_seconds=1, minimum_local_cadence_seconds=1)
