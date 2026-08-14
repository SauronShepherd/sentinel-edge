import pytest

from sentinel_edge.qualification.nts_state import NtsState


def test_nts_failure_fallback_is_visible_and_not_trusted() -> None:
    state = NtsState(False, "certificate_expired", "ntp-fallback")
    assert state.decision() == {"nts_authenticated": False, "failure_reason": "certificate_expired", "fallback_mode": "ntp-fallback", "trusted_status": False}


def test_fallback_cannot_preserve_trusted_status() -> None:
    with pytest.raises(ValueError, match="trusted status"):
        NtsState(False, "server_unreachable", "fixture-fallback", True)
