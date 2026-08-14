"""Attributable metadata conflicts with fail-safe review state."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class MetadataDecision(StrEnum):
    ACCEPTED = "accepted"
    REVIEW_REQUIRED = "review_required"


@dataclass(frozen=True)
class MetadataAssertion:
    source: str
    value: Any


@dataclass(frozen=True)
class MetadataResolution:
    field: str
    assertions: tuple[MetadataAssertion, ...]
    decision: MetadataDecision
    value: Any = None


def resolve_metadata(field: str, assertions: tuple[MetadataAssertion, ...] | list[MetadataAssertion], *, precedence: tuple[str, ...] = ()) -> MetadataResolution:
    rows = tuple(assertions)
    if not field.strip() or not rows or any(not row.source.strip() for row in rows):
        raise ValueError("metadata field and attributable assertions are required")
    values = {repr(row.value) for row in rows}
    if len(values) > 1:
        return MetadataResolution(field, rows, MetadataDecision.REVIEW_REQUIRED)
    if precedence:
        for source in precedence:
            for row in rows:
                if row.source == source:
                    return MetadataResolution(field, rows, MetadataDecision.ACCEPTED, row.value)
    return MetadataResolution(field, rows, MetadataDecision.ACCEPTED, rows[0].value)
