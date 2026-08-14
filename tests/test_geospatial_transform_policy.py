from sentinel_edge.geospatial.contracts import SpatialDecision, validate_geojson_geometry


def test_unqualified_transform_is_review_and_preserves_operation_trace() -> None:
    report = validate_geojson_geometry({"type": "Point", "coordinates": [1, 2]}, source_crs="EPSG:25830", transform_pipeline="pipeline:pinned-v1")
    assert report.decision is SpatialDecision.REVIEW_REQUIRED
    assert "unqualified_transform_operation" in report.reason_codes
    assert report.transform_pipeline == "pipeline:pinned-v1"


def test_ballpark_like_missing_operation_cannot_be_valid() -> None:
    report = validate_geojson_geometry({"type": "Point", "coordinates": [1, 2]}, source_crs="EPSG:9999", transform_pipeline="ballpark:identity")
    assert report.decision is SpatialDecision.REVIEW_REQUIRED
    assert report.normalized_geometry is None
