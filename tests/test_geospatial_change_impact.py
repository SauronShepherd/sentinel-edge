import pytest

from sentinel_edge.geospatial.change_impact import GeospatialChangeImpact


def test_geospatial_change_maps_operations_tests_and_claims() -> None:
    impact = GeospatialChangeImpact("c1", "proj.db", ("pipeline-1",), ("TEST-GRP-011",), ("claim-1",))
    assert impact.claim_impact()["rerun_required"] is True
    assert impact.claim_impact()["tests"] == ["TEST-GRP-011"]


def test_material_change_without_test_mapping_is_rejected() -> None:
    with pytest.raises(ValueError, match="operations and tests"):
        GeospatialChangeImpact("c1", "grid", (), (), (), True)
