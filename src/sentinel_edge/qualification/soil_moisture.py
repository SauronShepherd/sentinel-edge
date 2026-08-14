"""Deterministic soil-moisture trend metadata for landslide context."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SoilMoistureSample(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observed_at: datetime
    received_at: datetime
    fraction: float = Field(ge=0.0, le=1.0)
    resolution_m: float = Field(gt=0.0)
    source_id: str


class SoilMoistureTrend(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    sample_count: int = Field(ge=1)
    latest_fraction: float = Field(ge=0.0, le=1.0)
    delta_fraction: float
    slope_fraction_per_hour: float
    freshness_seconds: float = Field(ge=0.0)
    resolution_m: float
    fresh: bool
    trend: str


def assess_soil_moisture_trend(
    samples: tuple[SoilMoistureSample, ...],
    *,
    now: datetime,
    max_age_seconds: float,
) -> SoilMoistureTrend:
    if not samples:
        raise ValueError("at least one soil-moisture sample is required")
    if max_age_seconds <= 0 or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("positive freshness window and timezone-aware now are required")
    ordered = tuple(sorted(samples, key=lambda item: item.observed_at))
    if len({item.source_id for item in ordered}) != 1:
        raise ValueError("samples must have one source_id")
    if any(item.observed_at.tzinfo is None or item.received_at.tzinfo is None for item in ordered):
        raise ValueError("sample timestamps must be timezone-aware")
    if any(item.received_at < item.observed_at for item in ordered):
        raise ValueError("received_at cannot precede observed_at")
    first, latest = ordered[0], ordered[-1]
    elapsed_hours = (latest.observed_at - first.observed_at).total_seconds() / 3600.0
    delta = latest.fraction - first.fraction
    slope = delta / elapsed_hours if elapsed_hours > 0 else 0.0
    age = max(0.0, (now - latest.observed_at).total_seconds())
    trend = "rising" if delta > 0 else "falling" if delta < 0 else "stable"
    return SoilMoistureTrend(
        source_id=latest.source_id, sample_count=len(ordered), latest_fraction=latest.fraction,
        delta_fraction=delta, slope_fraction_per_hour=slope, freshness_seconds=age,
        resolution_m=latest.resolution_m, fresh=age <= max_age_seconds, trend=trend,
    )
