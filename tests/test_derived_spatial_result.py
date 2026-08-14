import pytest

from sentinel_edge.geospatial.derived_result import DerivedSpatialResult


def test_derived_result_preserves_operation_and_grid_provenance() -> None:
    result = DerivedSpatialResult((1.0, 2.0), "pipeline:pinned", ("grid-a",), 0.5)
    assert result.provenance() == {"operation": "pipeline:pinned", "grid_identities": ["grid-a"], "accuracy_m": 0.5}


def test_derived_result_rejects_missing_provenance() -> None:
    with pytest.raises(ValueError, match="operation and grid"):
        DerivedSpatialResult(1, "", (), 0.0)
