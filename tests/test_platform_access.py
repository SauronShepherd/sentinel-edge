import pytest

from sentinel_edge.qualification.platform_access import PlatformAccessStatus


def test_platform_access_exposes_eligibility_lag_and_media_availability() -> None:
    status = PlatformAccessStatus(platform="TikTok", creator_or_research_eligible=True,
        api_lag_seconds=45, media_bytes_available=False, access_basis="authorized-research-fixture")
    assert status.api_lag_seconds == 45
    assert status.media_bytes_available is False
    assert status.real_time_assumed is False


def test_platform_status_rejects_unauthorized_bytes_and_realtime_claims() -> None:
    with pytest.raises(ValueError):
        PlatformAccessStatus(platform="TikTok", creator_or_research_eligible=False,
            media_bytes_available=True, access_basis="fixture")
    with pytest.raises(ValueError):
        PlatformAccessStatus(platform="TikTok", creator_or_research_eligible=True,
            media_bytes_available=False, real_time_assumed=True, access_basis="api")
