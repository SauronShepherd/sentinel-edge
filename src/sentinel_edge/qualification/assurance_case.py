"""Typed, deterministic assurance-case records and closure checks."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator
from enum import StrEnum


class AssuranceClaim(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_id: str
    hazard_id: str
    control_id: str
    test_ids: tuple[str, ...] = Field(min_length=1)
    evidence_ids: tuple[str, ...] = Field(min_length=1)
    residual_limitation: str

    @model_validator(mode="after")
    def require_complete_links(self) -> "AssuranceClaim":
        if any(not value.strip() for value in (self.claim_id, self.hazard_id, self.control_id, self.residual_limitation)):
            raise ValueError("assurance claim identifiers and residual limitation are required")
        return self


class AssuranceCase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "sentinel-edge-assurance-case/1.0"
    claims: tuple[AssuranceClaim, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_claims(self) -> "AssuranceCase":
        ids = [item.claim_id for item in self.claims]
        if len(ids) != len(set(ids)):
            raise ValueError("assurance claim identifiers must be unique")
        return self


class ClosureState(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class ClosureDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    state: ClosureState
    evidence_ids: tuple[str, ...] = ()
    accepted_debt_id: str | None = None
    reason: str


def evaluate_closure(*, evidence_ids: tuple[str, ...] = (), accepted_debt_id: str | None = None) -> ClosureDecision:
    """Close only with non-empty evidence or an explicit accepted-debt record."""
    usable_evidence = tuple(item for item in evidence_ids if item.strip())
    debt = accepted_debt_id.strip() if accepted_debt_id else None
    if not usable_evidence and not debt:
        return ClosureDecision(state=ClosureState.OPEN, reason="closure_requires_evidence_or_accepted_debt")
    if usable_evidence:
        return ClosureDecision(state=ClosureState.CLOSED, evidence_ids=usable_evidence, accepted_debt_id=debt, reason="evidence_present")
    return ClosureDecision(state=ClosureState.CLOSED, accepted_debt_id=debt, reason="explicit_accepted_debt")
