import pytest

from sentinel_edge.qualification.exposure_context import ExposureContextAsset


def test_preclipped_attributed_exposure_context_is_non_authoritative() -> None:
    asset = ExposureContextAsset("worldpop-cell-1", "worldpop", "WorldPop 2025", True, True)
    assert asset.decision_scope() == "potential_exposure_context_only"


def test_live_or_unattributed_exposure_context_is_rejected() -> None:
    with pytest.raises(ValueError, match="preclipped"):
        ExposureContextAsset("osm-1", "osm", "OSM", False, True)
    with pytest.raises(ValueError, match="attribution"):
        ExposureContextAsset("ghsl-1", "ghsl", "", True, True)
