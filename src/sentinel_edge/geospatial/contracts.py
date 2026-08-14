from __future__ import annotations

import math
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SpatialDecision(StrEnum):
    VALID = "valid"
    REVIEW_REQUIRED = "review_required"
    REJECTED = "rejected"
    OVERLAP = "overlap"
    SEPARATE = "separate"
    UNCERTAIN = "uncertain"


class GeoPoint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    longitude: float = Field(ge=-180.0, le=180.0)
    latitude: float = Field(ge=-90.0, le=90.0)
    horizontal_uncertainty_m: float = Field(default=0.0, ge=0.0)
    source_crs: str = "EPSG:4326"
    source_axis_order: str = "longitude_latitude"
    transform_pipeline: str = "identity:EPSG:4326"
    transform_accuracy_m: float = Field(default=0.0, ge=0.0)
    area_of_use: str = "global"
    coordinate_epoch: float | None = None

    @field_validator("source_crs", "source_axis_order", "transform_pipeline", "area_of_use")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("spatial provenance fields must not be blank")
        return value


class VerticalReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    datum_id: str
    unit: str = "m"
    uncertainty_m: float | None = Field(default=None, ge=0.0)
    qualified: bool = False

    @field_validator("datum_id", "unit")
    @classmethod
    def vertical_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("vertical reference fields must not be blank")
        return value


class SpatialValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decision: SpatialDecision
    geometry_type: str
    coordinate_count: int = Field(ge=0)
    antimeridian_crossing: bool
    normalized_geometry: dict[str, Any] | None = None
    source_crs: str
    source_axis_order: str
    transform_pipeline: str
    reason_codes: tuple[str, ...]


class SpatialOverlapReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decision: SpatialDecision
    center_distance_m: float = Field(ge=0.0)
    minimum_possible_distance_m: float = Field(ge=0.0)
    maximum_possible_distance_m: float = Field(ge=0.0)
    threshold_m: float = Field(ge=0.0)
    reason_codes: tuple[str, ...]


def _iter_positions(geometry: dict[str, Any]) -> list[tuple[float, float]]:
    kind = geometry.get("type")
    coords = geometry.get("coordinates")
    if kind == "Point":
        candidates = [coords]
    elif kind == "LineString":
        candidates = coords
    elif kind == "Polygon":
        candidates = [p for ring in coords for p in ring]
    elif kind == "MultiPoint":
        candidates = coords
    elif kind == "MultiLineString":
        candidates = [p for line in coords for p in line]
    elif kind == "MultiPolygon":
        candidates = [p for polygon in coords for ring in polygon for p in ring]
    else:
        raise ValueError("unsupported GeoJSON geometry type")
    out: list[tuple[float, float]] = []
    for pos in candidates:
        if not isinstance(pos, (list, tuple)) or len(pos) < 2:
            raise ValueError("coordinate must contain longitude and latitude")
        lon, lat = pos[0], pos[1]
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise ValueError("coordinates must be numeric")
        out.append((float(lon), float(lat)))
    return out


def validate_geojson_geometry(
    geometry: dict[str, Any],
    *,
    source_crs: str = "EPSG:4326",
    source_axis_order: str = "longitude_latitude",
    transform_pipeline: str = "identity:EPSG:4326",
    max_coordinates: int = 10_000,
) -> SpatialValidationReport:
    reasons: list[str] = []
    kind = str(geometry.get("type", "unknown"))
    if source_crs != "EPSG:4326":
        return SpatialValidationReport(
            decision=SpatialDecision.REVIEW_REQUIRED,
            geometry_type=kind,
            coordinate_count=0,
            antimeridian_crossing=False,
            normalized_geometry=None,
            source_crs=source_crs,
            source_axis_order=source_axis_order,
            transform_pipeline=transform_pipeline,
            reason_codes=("unqualified_transform_operation", "transform_network_access_disabled"),
        )
    if source_axis_order != "longitude_latitude":
        return SpatialValidationReport(
            decision=SpatialDecision.REJECTED,
            geometry_type=kind,
            coordinate_count=0,
            antimeridian_crossing=False,
            normalized_geometry=None,
            source_crs=source_crs,
            source_axis_order=source_axis_order,
            transform_pipeline=transform_pipeline,
            reason_codes=("rfc7946_axis_order_required", "silent_axis_swap_rejected"),
        )
    try:
        positions = _iter_positions(geometry)
    except (TypeError, ValueError) as exc:
        return SpatialValidationReport(
            decision=SpatialDecision.REJECTED,
            geometry_type=kind,
            coordinate_count=0,
            antimeridian_crossing=False,
            normalized_geometry=None,
            source_crs=source_crs,
            source_axis_order=source_axis_order,
            transform_pipeline=transform_pipeline,
            reason_codes=(f"geometry_invalid:{exc}",),
        )
    if len(positions) > max_coordinates:
        reasons.append("geometry_complexity_exceeded")
    for lon, lat in positions:
        if not -180.0 <= lon <= 180.0 or not -90.0 <= lat <= 90.0:
            reasons.append("coordinate_out_of_bounds")
        if abs(lon) <= 90 and abs(lat) > 90:
            reasons.append("probable_axis_swap")
    if kind == "Polygon":
        for ring in geometry["coordinates"]:
            if len(ring) < 4 or ring[0][:2] != ring[-1][:2]:
                reasons.append("polygon_ring_not_closed")
    antimeridian = any(abs(a[0] - b[0]) > 180.0 for a, b in zip(positions, positions[1:]))
    if antimeridian:
        reasons.append("antimeridian_crossing_explicit")
    decision = SpatialDecision.REJECTED if any(
        code in reasons for code in ("geometry_complexity_exceeded", "coordinate_out_of_bounds", "probable_axis_swap", "polygon_ring_not_closed")
    ) else SpatialDecision.VALID
    if decision is SpatialDecision.VALID:
        reasons.append("rfc7946_geometry_valid")
    return SpatialValidationReport(
        decision=decision,
        geometry_type=kind,
        coordinate_count=len(positions),
        antimeridian_crossing=antimeridian,
        normalized_geometry=geometry if decision is SpatialDecision.VALID else None,
        source_crs=source_crs,
        source_axis_order=source_axis_order,
        transform_pipeline=transform_pipeline,
        reason_codes=tuple(sorted(set(reasons))),
    )


def geodesic_distance_m(left: GeoPoint, right: GeoPoint) -> float:
    """Haversine distance. Never interprets degree deltas as metres."""
    radius = 6_371_008.8
    lat1 = math.radians(left.latitude)
    lat2 = math.radians(right.latitude)
    dlat = lat2 - lat1
    dlon = math.radians(right.longitude - left.longitude)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * radius * math.asin(min(1.0, math.sqrt(a)))


def evaluate_uncertain_overlap(left: GeoPoint, right: GeoPoint, *, threshold_m: float) -> SpatialOverlapReport:
    distance = geodesic_distance_m(left, right)
    uncertainty = (
        left.horizontal_uncertainty_m + right.horizontal_uncertainty_m
        + left.transform_accuracy_m + right.transform_accuracy_m
    )
    minimum = max(0.0, distance - uncertainty)
    maximum = distance + uncertainty
    if maximum <= threshold_m:
        decision = SpatialDecision.OVERLAP
        reasons = ("overlap_proven_with_uncertainty",)
    elif minimum > threshold_m:
        decision = SpatialDecision.SEPARATE
        reasons = ("separation_proven_with_uncertainty",)
    else:
        decision = SpatialDecision.UNCERTAIN
        reasons = ("borderline_overlap_requires_review", "uncertainty_preserved")
    return SpatialOverlapReport(
        decision=decision,
        center_distance_m=distance,
        minimum_possible_distance_m=minimum,
        maximum_possible_distance_m=maximum,
        threshold_m=threshold_m,
        reason_codes=reasons,
    )


def compatible_vertical_references(left: VerticalReference, right: VerticalReference) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if left.unit != right.unit:
        reasons.append("vertical_unit_mismatch")
    if left.datum_id != right.datum_id:
        reasons.append("vertical_datum_mismatch")
    if not left.qualified or not right.qualified:
        reasons.append("vertical_datum_unqualified")
    return not reasons, tuple(sorted(reasons or ["vertical_reference_compatible"]))
