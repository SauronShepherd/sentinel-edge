import pytest

from sentinel_edge.qualification.lhasa_assets import LhasaContextAssetCard


def test_lhasa_asset_card_preserves_caveats_and_context_role() -> None:
    card = LhasaContextAssetCard("NASA LHASA", "L4 v2.0.0", "offline-context", "historical archive; delayed coverage", "archive differs from catalog")
    assert card.as_card()["local_truth_authority"] is False
    assert card.as_card()["archive_catalog_mismatch"] == "archive differs from catalog"


def test_context_asset_cannot_claim_local_truth() -> None:
    with pytest.raises(ValueError, match="local-truth"):
        LhasaContextAssetCard("IMERG/LHASA Exposure Maps", "1.0", "offline-context", "daily", local_truth_authority=True)
