"""Versioned source processing class and transition policy."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum


class ProcessingClass(StrEnum):
    OPERATIONAL_NRT = "operational_nrt"
    STANDARD_SCIENCE = "standard_science"
    HISTORICAL = "historical"


@dataclass(frozen=True)
class SourceProduct:
    source_id: str
    interface_version: str
    product_version: str
    terms_fingerprint: str
    processing_class: ProcessingClass
    origin_centre: str = ""
    topic: str = ""
    metadata_id: str = ""
    licence_id: str = ""
    interface_fingerprint: str = ""
    terms_reviewed_at: datetime | None = None

    def __post_init__(self) -> None:
        if any(not value.strip() for value in (self.source_id, self.interface_version, self.product_version, self.terms_fingerprint, self.interface_fingerprint, self.licence_id)):
            raise ValueError("source identity, interface, licence, and terms fingerprints are required")
        if self.terms_reviewed_at is None:
            raise ValueError("source terms review date is required")
        if self.terms_reviewed_at.tzinfo is None:
            raise ValueError("source terms review date must be timezone-aware")
        if self.terms_reviewed_at > datetime.now(timezone.utc):
            raise ValueError("source terms review date cannot be in the future")


@dataclass(frozen=True)
class SourceTransition:
    previous: SourceProduct
    current: SourceProduct
    review_required: bool
    reason_codes: tuple[str, ...]


def evaluate_source_transition(previous: SourceProduct, current: SourceProduct) -> SourceTransition:
    reasons = []
    if previous.interface_version != current.interface_version: reasons.append("interface_version_changed")
    if previous.product_version != current.product_version: reasons.append("product_version_changed")
    if previous.terms_fingerprint != current.terms_fingerprint: reasons.append("terms_fingerprint_changed")
    if previous.processing_class != current.processing_class: reasons.append("processing_class_changed")
    return SourceTransition(previous, current, bool(reasons), tuple(reasons) or ("source_continuity_verified",))
