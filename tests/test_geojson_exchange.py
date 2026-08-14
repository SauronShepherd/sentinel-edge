import pytest

from sentinel_edge.geospatial import build_geojson_exchange


def test_geojson_exchange_has_explicit_schema_and_coordinate_reference() -> None:
    exchange = build_geojson_exchange(
        {"type": "Point", "coordinates": [2.17, 41.38]},
        properties={"source": "local-sensor"},
    )
    assert exchange.schema == "sentinel-edge-geojson-exchange/1.0"
    assert exchange.crs == "EPSG:4326"
    assert exchange.axis_order == "longitude_latitude"
    assert exchange.coordinate_count == 1
    assert exchange.properties["source"] == "local-sensor"


def test_geojson_exchange_rejects_unqualified_crs_and_oversized_geometry() -> None:
    with pytest.raises(ValueError, match="GeoJSON exchange rejected"):
        build_geojson_exchange({"type": "Point", "coordinates": [2.0, 41.0]}, crs="EPSG:3857")
    with pytest.raises(ValueError, match="GeoJSON exchange rejected"):
        build_geojson_exchange({"type": "MultiPoint", "coordinates": [[1.0, 2.0], [3.0, 4.0]]}, max_coordinates=1)
