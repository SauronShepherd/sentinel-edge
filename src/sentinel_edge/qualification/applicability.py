"""Explicit applicability-domain checks for model and dataset claims."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ApplicabilityDisposition(StrEnum):
    ALLOW = "allow"
    ABSTAIN = "abstain"
    DEGRADE = "degrade"
    REVIEW_REQUIRED = "review_required"


@dataclass(frozen=True)
class ApplicabilityDomain:
    geography: frozenset[str]
    sensors: frozenset[str]
    seasons: frozenset[str]
    hazard_stages: frozenset[str]
    label_process: str

    def __post_init__(self) -> None:
        if not self.geography or not self.sensors or not self.seasons or not self.hazard_stages or not self.label_process.strip():
            raise ValueError("applicability domain must declare every dimension")


@dataclass(frozen=True)
class ApplicabilityEvidence:
    geography: str
    sensor: str
    season: str
    hazard_stage: str
    label_process: str


@dataclass(frozen=True)
class ApplicabilityDecision:
    disposition: ApplicabilityDisposition
    target_domain_evidence: bool
    reason_codes: tuple[str, ...]


def evaluate_applicability(domain: ApplicabilityDomain, evidence: ApplicabilityEvidence, *, request_transfer_claim: bool = False) -> ApplicabilityDecision:
    mismatches = []
    if evidence.geography not in domain.geography: mismatches.append("geography_out_of_domain")
    if evidence.sensor not in domain.sensors: mismatches.append("sensor_out_of_domain")
    if evidence.season not in domain.seasons: mismatches.append("season_out_of_domain")
    if evidence.hazard_stage not in domain.hazard_stages: mismatches.append("hazard_stage_out_of_domain")
    if evidence.label_process != domain.label_process: mismatches.append("label_process_mismatch")
    if mismatches:
        disposition = ApplicabilityDisposition.REVIEW_REQUIRED if request_transfer_claim else ApplicabilityDisposition.ABSTAIN
        return ApplicabilityDecision(disposition, False, tuple(mismatches))
    return ApplicabilityDecision(ApplicabilityDisposition.ALLOW, True, ("target_domain_evidence_present",))
