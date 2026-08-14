from sentinel_edge.geospatial.contracts import SpatialDecision, validate_geojson_geometry


def test_missing_required_operation_cannot_produce_normalized_decision_geometry() -> None:
    report = validate_geojson_geometry(
        {"type": "Point", "coordinates": [10, 20]},
        source_crs="EPSG:4258",
        transform_pipeline="",
    )
    assert report.decision is SpatialDecision.REVIEW_REQUIRED
    assert report.normalized_geometry is None
    assert "transform_network_access_disabled" in report.reason_codes
