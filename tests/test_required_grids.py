from sentinel_edge.geospatial.transform_declarations import validate_required_grids


def test_required_grid_identity_is_pinned() -> None:
    assert validate_required_grids(selected_operation="pipeline:ntv2", selected_grids=frozenset({"grid-a"}), required_grids=frozenset({"grid-a"})) == (True, ())


def test_missing_grid_and_fallback_are_rejected() -> None:
    ok, reasons = validate_required_grids(selected_operation="ballpark:identity", selected_grids=frozenset(), required_grids=frozenset({"grid-a"}))
    assert not ok
    assert reasons == ("unexpected_fallback_operation", "required_grid_missing:grid-a")
