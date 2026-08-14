"""Independent provider advisory and fixture invalidation decisions."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ProviderAdvisory(StrEnum):
    NORMAL = "normal"
    DEGRADED = "degraded"
    OUTAGE = "outage"


class SourceCompleteness(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


def assess_source_completeness(*, transport_status: int, expected_items: int | None, received_items: int | None) -> SourceCompleteness:
    """Assess scientific coverage independently from HTTP transport success."""
    if transport_status < 200 or transport_status >= 300:
        return SourceCompleteness.UNKNOWN
    if expected_items is None or received_items is None or expected_items <= 0 or received_items < 0:
        return SourceCompleteness.UNKNOWN
    if received_items < expected_items:
        return SourceCompleteness.PARTIAL
    return SourceCompleteness.COMPLETE


@dataclass(frozen=True)
class SourceQualityAssessment:
    reachable: bool
    complete: bool
    fresh: bool
    provider_advisory: ProviderAdvisory

    @property
    def healthy(self) -> bool:
        return self.reachable and self.complete and self.fresh and self.provider_advisory is ProviderAdvisory.NORMAL

    def reason_codes(self) -> tuple[str, ...]:
        reasons = []
        if not self.reachable: reasons.append("transport_unreachable")
        if not self.complete: reasons.append("coverage_incomplete")
        if not self.fresh: reasons.append("freshness_invalid")
        if self.provider_advisory is not ProviderAdvisory.NORMAL: reasons.append(f"provider_advisory:{self.provider_advisory.value}")
        return tuple(reasons) or ("source_healthy",)


@dataclass(frozen=True)
class FixtureInvalidation:
    invalidated: bool
    reason_codes: tuple[str, ...]


def invalidate_fixture_on_transition(previous_fingerprint: str, current_fingerprint: str) -> FixtureInvalidation:
    if not previous_fingerprint.strip() or not current_fingerprint.strip():
        raise ValueError("source fingerprints are required")
    if previous_fingerprint == current_fingerprint:
        return FixtureInvalidation(False, ("source_fingerprint_unchanged",))
    return FixtureInvalidation(True, ("source_transition_detected", "fixture_requalification_required"))
