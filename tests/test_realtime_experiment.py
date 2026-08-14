import pytest

from sentinel_edge.qualification.realtime_experiment import timebox_realtime_experiment


def test_watchdog_timeboxes_privileged_experiment_without_replacing_default_proof() -> None:
    result = timebox_realtime_experiment("sched-exp", elapsed_seconds=2.0, timeout_seconds=1.0)
    assert result.watchdog_expired is True
    assert result.replaces_default_proof is False
    assert result.elapsed_seconds == 1.0


def test_replacing_default_proof_is_rejected() -> None:
    with pytest.raises(ValueError, match="replace default proof"):
        # The public result type remains fail-closed if a caller tries to forge this state.
        from sentinel_edge.qualification.realtime_experiment import RealtimeExperimentResult
        RealtimeExperimentResult("sched-exp", 1.0, False, replaces_default_proof=True)
