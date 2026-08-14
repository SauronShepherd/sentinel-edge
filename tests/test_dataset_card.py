import pytest

from sentinel_edge.qualification.dataset_card import DatasetCard


def test_dataset_card_records_actual_downloadable_asset_license() -> None:
    card = DatasetCard(dataset_id="uglc", dataset_name="UGLC records",
        downloadable_asset_license="CC-BY-4.0", provenance="fixture:uglc")
    assert card.downloadable_asset_license == "CC-BY-4.0"


def test_dataset_card_rejects_unresolved_license() -> None:
    with pytest.raises(ValueError):
        DatasetCard(dataset_id="x", dataset_name="x", downloadable_asset_license="NOASSERTION", provenance="fixture")
