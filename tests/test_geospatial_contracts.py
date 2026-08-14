from sentinel_edge.geospatial import (
    GeoPoint,
    SpatialDecision,
    VerticalReference,
    compatible_vertical_references,
    evaluate_uncertain_overlap,
    geodesic_distance_m,
    validate_geojson_geometry,
)


def test_rfc7946_axis_swap_and_invalid_polygon_are_rejected() -> None:
    swapped = validate_geojson_geometry(
        {"type": "Point", "coordinates": [40.0, -120.0]},
        source_axis_order="latitude_longitude",
    )
    assert swapped.decision is SpatialDecision.REJECTED
    assert "silent_axis_swap_rejected" in swapped.reason_codes
    polygon = validate_geojson_geometry(
        {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1]]]},
    )
    assert polygon.decision is SpatialDecision.REJECTED
    assert "polygon_ring_not_closed" in polygon.reason_codes


def test_antimeridian_is_explicit_and_non_4326_requires_review() -> None:
    crossing = validate_geojson_geometry(
        {"type": "LineString", "coordinates": [[179.5, 10.0], [-179.5, 10.0]]},
    )
    assert crossing.decision is SpatialDecision.VALID
    assert crossing.antimeridian_crossing is True
    projected = validate_geojson_geometry(
        {"type": "Point", "coordinates": [500000, 4500000]}, source_crs="EPSG:32630"
    )
    assert projected.decision is SpatialDecision.REVIEW_REQUIRED
    assert "transform_network_access_disabled" in projected.reason_codes


def test_metric_distance_is_geodesic_and_uncertainty_is_preserved() -> None:
    left = GeoPoint(longitude=0.0, latitude=0.0, horizontal_uncertainty_m=80.0)
    right = GeoPoint(longitude=0.001, latitude=0.0, horizontal_uncertainty_m=80.0)
    distance = geodesic_distance_m(left, right)
    assert 110.0 < distance < 112.0
    report = evaluate_uncertain_overlap(left, right, threshold_m=100.0)
    assert report.decision is SpatialDecision.UNCERTAIN
    assert "uncertainty_preserved" in report.reason_codes


def test_mixed_vertical_datum_cannot_create_threshold_decision() -> None:
    left = VerticalReference(datum_id="EPSG:5703", qualified=True)
    right = VerticalReference(datum_id="local-gauge-zero", qualified=True)
    compatible, reasons = compatible_vertical_references(left, right)
    assert compatible is False
    assert "vertical_datum_mismatch" in reasons
