from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sentinel_edge.domain.models import CapabilityState
from sentinel_edge.security import canonical_json_bytes, sha256_bytes


QUALIFICATION_VOCABULARY: tuple[str, ...] = (
    CapabilityState.SPECIFIED.value,
    CapabilityState.IMPLEMENTED.value,
    CapabilityState.TESTED.value,
    CapabilityState.TARGET_QUALIFIED.value,
    CapabilityState.RELEASE_ADMITTED.value,
    CapabilityState.FIELD_QUALIFIED.value,
    CapabilityState.DEFERRED.value,
    CapabilityState.BLOCKED.value,
    CapabilityState.FAILED.value,
    CapabilityState.EXPIRED.value,
)

_STATE_STRENGTH = {
    CapabilityState.SPECIFIED: 0,
    CapabilityState.DEFERRED: 0,
    CapabilityState.IMPLEMENTED: 1,
    CapabilityState.TESTED: 2,
    CapabilityState.TARGET_QUALIFIED: 3,
    CapabilityState.FIELD_QUALIFIED: 4,
    CapabilityState.RELEASE_ADMITTED: 5,
    CapabilityState.BLOCKED: -1,
    CapabilityState.FAILED: -1,
    CapabilityState.EXPIRED: -1,
}


class QualificationDomain(StrEnum):
    TARGET = "target"
    SOURCE = "source"
    MODEL = "model"
    CALIBRATION = "calibration"
    SECURITY = "security"
    PLATFORM = "platform"


class EvidenceProvenance(StrEnum):
    OBSERVED = "observed"
    MEASURED = "measured"
    FIXTURE = "fixture"
    MIGRATED = "migrated"
    RECONSTRUCTED = "reconstructed"


class QualificationEvidenceWindow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_: Literal["sentinel-edge-qualification-evidence-window/1.0"] = Field(
        default="sentinel-edge-qualification-evidence-window/1.0", alias="schema", serialization_alias="schema"
    )
    qualification_id: str
    domain: QualificationDomain
    subject_id: str
    state: CapabilityState
    evidence_sha256: str
    valid_from: datetime
    valid_until: datetime
    provenance: EvidenceProvenance
    target_binding_sha256: str | None = None
    limitations: tuple[str, ...] = ()
    reconstructed_missing_fields: tuple[str, ...] = ()

    @field_validator("qualification_id", "subject_id", "evidence_sha256")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("qualification identifiers must not be blank")
        return value

    @model_validator(mode="after")
    def validate_window(self) -> "QualificationEvidenceWindow":
        if self.valid_until <= self.valid_from:
            raise ValueError("qualification evidence window must have positive duration")
        if self.provenance in {EvidenceProvenance.MIGRATED, EvidenceProvenance.RECONSTRUCTED}:
            if not self.reconstructed_missing_fields:
                raise ValueError("migrated or reconstructed qualification must identify missing historical proof")
            if self.state in {
                CapabilityState.TARGET_QUALIFIED,
                CapabilityState.FIELD_QUALIFIED,
                CapabilityState.RELEASE_ADMITTED,
            }:
                raise ValueError("reconstructed evidence cannot assert a qualified state")
        return self


class QualificationClaim(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    capability_id: str
    requested_state: CapabilityState
    statement: str

    @field_validator("capability_id", "statement")
    @classmethod
    def claim_text_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("claim fields must not be blank")
        return value


def evaluate_evidence_window(
    window: QualificationEvidenceWindow | dict[str, Any], *, now: datetime | None = None
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    item = window if isinstance(window, QualificationEvidenceWindow) else QualificationEvidenceWindow.model_validate(window)
    failures: list[str] = []
    limitations = list(item.limitations)
    effective_state = item.state
    if now < item.valid_from:
        failures.append("qualification_not_yet_valid")
        effective_state = CapabilityState.BLOCKED
    elif now >= item.valid_until:
        failures.append("qualification_expired")
        effective_state = CapabilityState.EXPIRED
    if item.provenance in {EvidenceProvenance.MIGRATED, EvidenceProvenance.RECONSTRUCTED}:
        failures.append("historical_proof_incomplete")
        limitations.extend(f"missing_historical_proof:{name}" for name in item.reconstructed_missing_fields)
        if _STATE_STRENGTH[effective_state] > _STATE_STRENGTH[CapabilityState.TESTED]:
            effective_state = CapabilityState.TESTED
    claim_allowed = effective_state in {
        CapabilityState.TARGET_QUALIFIED,
        CapabilityState.FIELD_QUALIFIED,
        CapabilityState.RELEASE_ADMITTED,
    }
    body = {
        "schema": "sentinel-edge-qualification-evidence-evaluation/1.0",
        "qualification_id": item.qualification_id,
        "domain": item.domain.value,
        "subject_id": item.subject_id,
        "declared_state": item.state.value,
        "effective_state": effective_state.value,
        "evidence_sha256": item.evidence_sha256,
        "target_binding_sha256": item.target_binding_sha256,
        "valid_from": item.valid_from.isoformat(),
        "valid_until": item.valid_until.isoformat(),
        "evaluated_at": now.isoformat(),
        "claim_allowed": claim_allowed,
        "failures": sorted(set(failures)),
        "limitations": sorted(set(limitations)),
        "provenance": item.provenance.value,
    }
    return {**body, "report_digest": sha256_bytes(canonical_json_bytes(body))}


def enforce_claim_ceiling(
    claim: QualificationClaim | dict[str, Any], evaluations: list[dict[str, Any]]
) -> dict[str, Any]:
    item = claim if isinstance(claim, QualificationClaim) else QualificationClaim.model_validate(claim)
    failures: list[str] = []
    effective_states: list[CapabilityState] = []
    for evaluation in evaluations:
        try:
            effective_states.append(CapabilityState(evaluation["effective_state"]))
        except (KeyError, ValueError):
            failures.append("qualification_evaluation_invalid")
    if not effective_states:
        failures.append("qualification_evidence_missing")
        ceiling = CapabilityState.SPECIFIED
    else:
        ceiling = min(effective_states, key=lambda state: _STATE_STRENGTH[state])
    allowed = not failures and _STATE_STRENGTH[item.requested_state] <= _STATE_STRENGTH[ceiling]
    if not allowed and not failures:
        failures.append("claim_exceeds_evidence_state")
    body = {
        "schema": "sentinel-edge-qualification-claim-decision/1.0",
        "capability_id": item.capability_id,
        "statement": item.statement,
        "requested_state": item.requested_state.value,
        "evidence_ceiling": ceiling.value,
        "allowed": allowed,
        "failures": sorted(set(failures)),
        "qualification_vocabulary": list(QUALIFICATION_VOCABULARY),
    }
    return {**body, "decision_digest": sha256_bytes(canonical_json_bytes(body))}


def qualification_vocabulary_report() -> dict[str, Any]:
    body = {
        "schema": "sentinel-edge-qualification-vocabulary/1.0",
        "states": list(QUALIFICATION_VOCABULARY),
        "unknown_values_rejected": True,
        "claim_ceiling_enforced": True,
    }
    return {**body, "report_digest": sha256_bytes(canonical_json_bytes(body))}
