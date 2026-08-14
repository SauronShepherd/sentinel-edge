import pytest
from pydantic import ValidationError

from sentinel_edge.gateway.network_policy import ExposureProfile, NetworkExposurePolicy


@pytest.mark.parametrize("profile", [ExposureProfile.LOCAL_ONLY, ExposureProfile.JUDGE, ExposureProfile.BENCHMARK])
def test_restricted_profiles_are_loopback_and_egress_denied(profile: ExposureProfile) -> None:
    policy = NetworkExposurePolicy(
        profile=profile, bind_host="127.0.0.1", auth_required=True, tls_required=False, egress_allowed=False
    )
    assert policy.model_dump(mode="json")["profile"] == profile.value


def test_trusted_lan_and_service_require_authenticated_tls() -> None:
    for profile, egress in ((ExposureProfile.TRUSTED_LAN, False), (ExposureProfile.SERVICE, True)):
        policy = NetworkExposurePolicy(
            profile=profile, bind_host="192.0.2.10", auth_required=True, tls_required=True, egress_allowed=egress
        )
        assert policy.tls_required is True


def test_invalid_bind_auth_and_egress_combinations_fail_closed() -> None:
    with pytest.raises(ValidationError):
        NetworkExposurePolicy(
            profile=ExposureProfile.LOCAL_ONLY, bind_host="0.0.0.0", auth_required=False, tls_required=False, egress_allowed=True
        )
    with pytest.raises(ValidationError):
        NetworkExposurePolicy(
            profile=ExposureProfile.TRUSTED_LAN, bind_host="192.0.2.10", auth_required=True, tls_required=False, egress_allowed=False
        )
