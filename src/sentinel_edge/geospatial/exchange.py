"""Bounded GeoJSON exchange envelope with explicit CRS provenance."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from sentinel_edge.geospatial.contracts import validate_geojson_geometry


class GeoJsonExchange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema: str = "sentinel-edge-geojson-exchange/1.0"
    type: str = "Feature"
    geometry: dict[str, Any]
    properties: dict[str, Any] = Field(default_factory=dict)
    crs: str = "EPSG:4326"
    axis_order: str = "longitude_latitude"
    transform_pipeline: str = "identity:EPSG:4326"
    coordinate_count: int = Field(ge=0)


def build_geojson_exchange(
    geometry: dict[str, Any],
    *,
    properties: dict[str, Any] | None = None,
    crs: str = "EPSG:4326",
    axis_order: str = "longitude_latitude",
    transform_pipeline: str = "identity:EPSG:4326",
    max_coordinates: int = 10_000,
) -> GeoJsonExchange:
    report = validate_geojson_geometry(
        geometry,
        source_crs=crs,
        source_axis_order=axis_order,
        transform_pipeline=transform_pipeline,
        max_coordinates=max_coordinates,
    )
    if report.decision.value != "valid":
        raise ValueError("GeoJSON exchange rejected: " + ",".join(report.reason_codes))
    return GeoJsonExchange(
        geometry=report.normalized_geometry or geometry,
        properties=properties or {},
        crs=report.source_crs,
        axis_order=report.source_axis_order,
        transform_pipeline=report.transform_pipeline,
        coordinate_count=report.coordinate_count,
    )
