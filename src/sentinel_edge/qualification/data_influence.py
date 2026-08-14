"""Explicit impact decisions for data rights and correction events."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class InfluenceAction(StrEnum):
    NO_IMPACT = "no_impact"
    RESTRICT = "restrict"
    WITHDRAW = "withdraw"
    RECOMPUTE = "recompute"
    RECALIBRATE = "recalibrate"
    RETRAIN = "retrain"
    SUPERSEDE = "supersede"
    REVIEW = "review"


@dataclass(frozen=True)
class InfluenceDecision:
    artifact_id: str
    action: InfluenceAction
    source_variant_id: str
    weight_level_removal: str
    reason: str

    def __post_init__(self) -> None:
        if any(not value.strip() for value in (self.artifact_id, self.source_variant_id, self.weight_level_removal, self.reason)):
            raise ValueError("influence decision fields are required")

    @property
    def promotion_allowed(self) -> bool:
        return self.action is InfluenceAction.NO_IMPACT


def assess_influence(*, artifact_id: str, source_variant_id: str, event: str, weight_level_removal: str = "unproven") -> InfluenceDecision:
    mapping = {"rights_withdrawn": InfluenceAction.WITHDRAW, "source_restricted": InfluenceAction.RESTRICT, "labels_corrected": InfluenceAction.RECALIBRATE, "dataset_retracted": InfluenceAction.REVIEW, "no_influence": InfluenceAction.NO_IMPACT}
    return InfluenceDecision(artifact_id, mapping.get(event, InfluenceAction.REVIEW), source_variant_id, weight_level_removal, f"event:{event}")
