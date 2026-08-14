"""Reference-only post-event corroboration for local earthquake observations."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ReferenceProvider(StrEnum):
    IGN = "IGN"
    USGS = "USGS"


class ReferenceEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: ReferenceProvider
    event_id: str
    occurred_at: datetime
    published_at: datetime | None = None
    magnitude: float | None = Field(default=None, ge=0.0)
    resolution_km: float | None = Field(default=None, ge=0.0)
    reference_url: str | None = None


class PostEventMatch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: ReferenceProvider
    event_id: str
    matched: bool
    event_offset_ms: float
    publication_delay_seconds: float | None = None
    resolution_km: float | None = None
    caveats: tuple[str, ...] = ()
    status: str
    reference_only: bool = True


class PostEventCorroborationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    local_observed_at: datetime
    tolerance_seconds: float = Field(gt=0.0)
    matches: tuple[PostEventMatch, ...]
    corroborated: bool
    providers_considered: tuple[ReferenceProvider, ...]
    classification: str = "reference_only"


def corroborate_post_event(
    local_observed_at: datetime,
    references: tuple[ReferenceEvent, ...],
    *,
    tolerance_seconds: float = 120.0,
) -> PostEventCorroborationReport:
    if tolerance_seconds <= 0:
        raise ValueError("tolerance_seconds must be positive")
    matches: list[PostEventMatch] = []
    for event in sorted(references, key=lambda item: (item.occurred_at, item.provider.value, item.event_id)):
        offset_seconds = (event.occurred_at - local_observed_at).total_seconds()
        matched = abs(offset_seconds) <= tolerance_seconds
        caveats: list[str] = ["reference_only_no_physical_truth_claim"]
        delay = None
        if event.published_at is None:
            caveats.append("publication_delay_unknown")
        else:
            delay = (event.published_at - event.occurred_at).total_seconds()
            if delay < 0:
                caveats.append("publication_time_precedes_event_time_invalid")
                matched = False
        if event.resolution_km is None:
            caveats.append("spatial_resolution_unknown")
        matches.append(PostEventMatch(
            provider=event.provider, event_id=event.event_id, matched=matched,
            event_offset_ms=offset_seconds * 1000, publication_delay_seconds=delay,
            resolution_km=event.resolution_km, caveats=tuple(sorted(caveats)),
            status="matched" if matched else "not_matched",
        ))
    return PostEventCorroborationReport(
        local_observed_at=local_observed_at,
        tolerance_seconds=tolerance_seconds,
        matches=tuple(matches),
        corroborated=any(item.matched for item in matches),
        providers_considered=tuple(sorted({item.provider for item in matches}, key=lambda item: item.value)),
    )
