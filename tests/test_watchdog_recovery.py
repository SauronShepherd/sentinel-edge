from datetime import datetime, timezone

import pytest

from sentinel_edge.runtime import WorkerRecoveryPolicy


def test_process_restart_is_bounded_and_hardware_watchdog_is_distinct() -> None:
    policy = WorkerRecoveryPolicy(max_restarts=2, window_seconds=60)
    at = datetime(2026, 8, 12, tzinfo=timezone.utc)
    assert policy.record_failure("wildfire", at=at).mechanism == "process_restart"
    assert policy.record_failure("wildfire", at=at).allowed is True
    blocked = policy.record_failure("wildfire", at=at)
    assert blocked.quarantined is True
    assert policy.hardware_watchdog_recovery("wildfire").allowed is False
    other = policy.hardware_watchdog_recovery("flood")
    assert other.mechanism == "hardware_watchdog"
    assert other.reason_code == "hardware_watchdog_recovery_distinct"


def test_recovery_requires_positive_bounds_and_aware_time() -> None:
    with pytest.raises(ValueError):
        WorkerRecoveryPolicy(max_restarts=0)
    policy = WorkerRecoveryPolicy()
    with pytest.raises(ValueError):
        policy.record_failure("x", at=datetime(2026, 8, 12))
