"""Bounded STAC Item metadata for satellite/context assets."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


SUPPORTED_COPERNICUS_INTERFACE_PREFIXES = (
    "https://catalogue.dataspace.copernicus.eu/stac",
    "https://catalogue.dataspace.copernicus.eu/odata",
)


def validate_copernicus_endpoint(endpoint: str) -> str:
    """Accept only the supported Copernicus STAC/OData interface families."""
    value = endpoint.strip()
    if not any(value.startswith(prefix) for prefix in SUPPORTED_COPERNICUS_INTERFACE_PREFIXES):
        raise ValueError("unsupported or deprecated Copernicus endpoint")
    return value


class StacAsset(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    href: str
    media_type: str
    roles: tuple[str, ...] = ()
    title: str | None = None

    @field_validator("href", "media_type")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("STAC asset fields must not be blank")
        return value


class StacItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    type: str = "Feature"
    stac_version: str = "1.0.0"
    id: str
    geometry: dict[str, Any] | None = None
    bbox: tuple[float, ...] | None = None
    datetime: datetime
    properties: dict[str, Any]
    assets: dict[str, StacAsset]
    license: str
    provenance: str
    source_class: str = "context_reference"

    @field_validator("id", "license", "provenance")
    @classmethod
    def required_metadata(cls, value: str) -> str:
        if not value.strip() or value.strip().upper() in {"NOASSERTION", "UNKNOWN", "UNLICENSED"}:
            raise ValueError("STAC provenance and resolved license are required")
        return value

    @field_validator("assets")
    @classmethod
    def bounded_assets(cls, value: dict[str, StacAsset]) -> dict[str, StacAsset]:
        if not value or len(value) > 64:
            raise ValueError("STAC item must contain 1..64 assets")
        return value


def build_stac_item(*, item_id: str, captured_at: datetime, assets: dict[str, StacAsset], license: str, provenance: str, geometry: dict[str, Any] | None = None, properties: dict[str, Any] | None = None) -> StacItem:
    return StacItem(id=item_id, datetime=captured_at, assets=assets, license=license, provenance=provenance, geometry=geometry, properties=properties or {})
