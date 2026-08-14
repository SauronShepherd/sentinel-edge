import pytest

from sentinel_edge.qualification.research_assets import AssetUse, ResearchAssetPolicy


def test_openhydronet_is_offline_research_only_until_independent_promotion() -> None:
    policy = ResearchAssetPolicy("OpenHydroNet", use=AssetUse.OFFLINE)
    assert policy.permits_incident_state() is False
    with pytest.raises(PermissionError):
        policy.assert_not_authoritative()
