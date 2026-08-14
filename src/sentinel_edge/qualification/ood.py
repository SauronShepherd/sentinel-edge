"""Conservative out-of-distribution handling for model or adapter outputs."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OODDisposition(StrEnum):
    ACCEPT = "accept"
    REVIEW_REQUIRED = "review_required"
    DEGRADED = "degraded"


class OODDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    input_id: str
    baseline_confidence: float = Field(ge=0.0, le=1.0)
    observed_confidence: float = Field(ge=0.0, le=1.0)
    out_of_distribution: bool
    disposition: OODDisposition
    coverage: str
    reason_codes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def enforce_conservative_handling(self) -> "OODDecision":
        if not self.input_id.strip() or not self.coverage.strip():
            raise ValueError("OOD decision identifiers must not be blank")
        if self.out_of_distribution:
            if self.observed_confidence > self.baseline_confidence:
                raise ValueError("OOD input cannot strengthen confidence")
            if self.disposition is OODDisposition.ACCEPT:
                raise ValueError("OOD input requires review or degraded disposition")
        return self

