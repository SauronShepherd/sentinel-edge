"""Deterministic adversarial campaign records for adapter qualification."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AdversarialCase(StrEnum):
    EVASION = "evasion"
    SPOOFING = "spoofing"
    POISONING = "poisoning"
    RESOURCE_EXHAUSTION = "resource_exhaustion"


class DefensiveOutcome(StrEnum):
    ABSTAIN = "abstain"
    DEGRADE = "degrade"
    REJECT = "reject"


class AdapterDefensiveResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    adapter_id: str
    case: AdversarialCase
    outcome: DefensiveOutcome
    reason_code: str
    test_id: str

    @model_validator(mode="after")
    def fields_present(self) -> "AdapterDefensiveResult":
        if any(not value.strip() for value in (self.adapter_id, self.reason_code, self.test_id)):
            raise ValueError("adversarial result identifiers must not be blank")
        return self


class AdversarialCampaign(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    results: tuple[AdapterDefensiveResult, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def require_representative_cases(self) -> "AdversarialCampaign":
        observed = {item.case for item in self.results}
        missing = set(AdversarialCase) - observed
        if missing:
            raise ValueError(f"adversarial campaign missing cases: {sorted(item.value for item in missing)}")
        return self

