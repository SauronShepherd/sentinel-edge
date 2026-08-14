"""Governed external context for landslide assessment; never incident truth."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LandslideContextKind(StrEnum):
    BD_MOVES_TERRAIN = "BD-MOVES/terrain"
    COPERNICUS_SOIL_WATER_INDEX = "Copernicus-SWI"
    EGMS_DEFORMATION = "EGMS"


class LandslideContextRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: LandslideContextKind
    record_id: str
    source_provenance: str
    observed_at: datetime
    received_at: datetime
    resolution_m: float | None = Field(default=None, gt=0.0)
    value: float | None = None
    historical_only: bool = False
    decision_influence_allowed: bool = False

    @model_validator(mode="after")
    def validate_context(self) -> "LandslideContextRecord":
        if not self.record_id.strip() or not self.source_provenance.strip():
            raise ValueError("context identity and provenance are required")
        if self.observed_at.tzinfo is None or self.received_at.tzinfo is None:
            raise ValueError("context timestamps must be timezone-aware")
        if self.received_at < self.observed_at:
            raise ValueError("received_at cannot precede observed_at")
        if self.kind is LandslideContextKind.EGMS_DEFORMATION and not self.historical_only:
            raise ValueError("EGMS deformation context must be historical-only")
        if self.decision_influence_allowed:
            raise ValueError("external landslide context cannot influence incident decisions")
        return self


class LandslideContextDisplay(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: LandslideContextKind
    record_id: str
    source_provenance: str
    age_seconds: float = Field(ge=0.0)
    resolution_m: float | None
    historical_only: bool
    decision_influence_allowed: bool = False


def display_landslide_context(record: LandslideContextRecord, *, now: datetime) -> LandslideContextDisplay:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    age = max(0.0, (now - record.observed_at).total_seconds())
    return LandslideContextDisplay(
        kind=record.kind, record_id=record.record_id, source_provenance=record.source_provenance,
        age_seconds=age, resolution_m=record.resolution_m, historical_only=record.historical_only,
    )
