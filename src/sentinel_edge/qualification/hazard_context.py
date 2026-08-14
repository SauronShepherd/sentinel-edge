"""Deterministic, reference-only hazard context qualification."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HazardContextProvider(StrEnum):
    AEMET = "AEMET"
    FIRMS = "FIRMS"
    EFFIS = "EFFIS"
    SAIH = "SAIH"
    CHJ = "CHJ"
    METEOALARM = "MeteoAlarm"


class HazardContextRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: HazardContextProvider
    record_id: str
    observed_at: datetime
    received_at: datetime
    resolution_km: float | None = Field(default=None, ge=0.0)
    source_url: str | None = None
    original_provenance: str


class HazardContextAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: HazardContextProvider
    record_id: str
    freshness_seconds: float
    fresh: bool
    resolution_km: float | None
    caveats: tuple[str, ...]
    reference_only: bool = True


class AuthorityNotice(BaseModel):
    """External warning/status context; never silently becomes local truth."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: HazardContextProvider
    notice_id: str
    issued_at: datetime
    status: str
    original_authority: str
    provisional: bool = True
    source_url: str | None = None

    @model_validator(mode="after")
    def validate_notice(self) -> "AuthorityNotice":
        if not self.notice_id.strip() or not self.original_authority.strip():
            raise ValueError("authority notice identity and authority are required")
        if self.issued_at.tzinfo is None or self.issued_at.utcoffset() is None:
            raise ValueError("authority notice timestamp must be timezone-aware")
        if not self.status.strip():
            raise ValueError("authority notice status is required")
        return self


def assess_hazard_context(
    records: tuple[HazardContextRecord, ...],
    *,
    now: datetime,
    max_age_seconds: float,
) -> tuple[HazardContextAssessment, ...]:
    """Return displayable freshness/caveat metadata without decision influence."""
    if max_age_seconds <= 0:
        raise ValueError("max_age_seconds must be positive")
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    result: list[HazardContextAssessment] = []
    for record in sorted(records, key=lambda item: (item.provider.value, item.record_id)):
        if record.observed_at.tzinfo is None or record.received_at.tzinfo is None:
            raise ValueError("context timestamps must be timezone-aware")
        age = (now - record.observed_at).total_seconds()
        caveats = ["reference_only_no_decision_influence"]
        if record.received_at < record.observed_at:
            caveats.append("received_before_observed_invalid")
        if record.received_at > now:
            caveats.append("received_in_future_invalid")
        if record.resolution_km is None:
            caveats.append("spatial_resolution_unknown")
        if not record.original_provenance.strip():
            caveats.append("original_provenance_missing")
        result.append(HazardContextAssessment(
            provider=record.provider,
            record_id=record.record_id,
            freshness_seconds=age,
            fresh=0 <= age <= max_age_seconds and not any(
                item.endswith("invalid") for item in caveats
            ),
            resolution_km=record.resolution_km,
            caveats=tuple(sorted(caveats)),
        ))
    return tuple(result)
