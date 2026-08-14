import pytest

from sentinel_edge.qualification.research_assets import AssetUse, ResearchAssetPolicy


def test_research_asset_cannot_drive_incident_or_h0_claims() -> None:
    asset = ResearchAssetPolicy("jrc-storyline-2026", use=AssetUse.EVALUATION_ONLY)
    assert asset.permits_incident_state() is False
    assert asset.permits_h0_quality_claim() is False
    with pytest.raises(PermissionError):
        asset.assert_not_authoritative()


def test_release_use_requires_promotion_gate() -> None:
    with pytest.raises(ValueError):
        ResearchAssetPolicy("impactmesh", use=AssetUse.RELEASED, promotion_gate_passed=False)
    released = ResearchAssetPolicy("impactmesh", use=AssetUse.RELEASED, promotion_gate_passed=True)
    assert released.permits_incident_state() is True
