"""Stable lineage fingerprints for governed source snapshots."""

import hashlib
import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SourceSnapshotLineage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    snapshot_id: str
    lineage_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    parent_product: str
    constellation: str | None = None
    algorithm_version: str
    parent_product_transition: str | None = None

    @model_validator(mode="after")
    def validate_lineage(self) -> "SourceSnapshotLineage":
        if any(not value.strip() for value in (self.source_id, self.snapshot_id, self.parent_product, self.algorithm_version)):
            raise ValueError("source lineage identity is required")
        return self


class LineageInfluenceDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decision_influence_allowed: bool
    reason: str


class LineageAggregationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    groups: dict[str, int]
    separated_transitions: bool

    @model_validator(mode="after")
    def validate_aggregation(self) -> "LineageAggregationReport":
        if not self.groups or any(count < 0 for count in self.groups.values()):
            raise ValueError("lineage aggregation groups are required")
        if not self.separated_transitions:
            raise ValueError("before/after lineage transitions must remain separated")
        return self


def evaluate_lineage_influence(expected: SourceSnapshotLineage, observed: SourceSnapshotLineage) -> LineageInfluenceDecision:
    if expected.lineage_fingerprint != observed.lineage_fingerprint:
        return LineageInfluenceDecision(decision_influence_allowed=False, reason="lineage_fingerprint_changed")
    if expected.parent_product != observed.parent_product or expected.constellation != observed.constellation:
        return LineageInfluenceDecision(decision_influence_allowed=False, reason="parent_or_constellation_changed")
    return LineageInfluenceDecision(decision_influence_allowed=True, reason="lineage_unchanged")


def fingerprint_source_snapshot(snapshot: dict[str, Any]) -> str:
    if not snapshot:
        raise ValueError("source snapshot cannot be empty")
    canonical = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
