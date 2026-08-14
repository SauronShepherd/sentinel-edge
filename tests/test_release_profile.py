import pytest

from sentinel_edge.release.profile import Capability, CapabilityState, ReleaseProfile


def test_release_profile_enumerates_all_states() -> None:
    profile = ReleaseProfile("H0-test", tuple(Capability(state.value, state, "declared") for state in CapabilityState))
    assert {item["state"] for item in profile.as_dict()["capabilities"]} == {state.value for state in CapabilityState}


def test_release_profile_rejects_missing_state() -> None:
    with pytest.raises(ValueError, match="every capability state"):
        ReleaseProfile("bad", (Capability("enabled", CapabilityState.ENABLED, "x"),))
