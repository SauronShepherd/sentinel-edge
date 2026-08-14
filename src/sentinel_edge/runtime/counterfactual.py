"""Offline diagnostics for retained skipped opportunities."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CounterfactualAudit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    opportunity_id: str
    disposition: str = "skipped"
    model_sha256: str
    config_sha256: str
    diagnostic_only: bool = True
    retained_input_ref: str
    result: dict[str, float | str]

    @model_validator(mode="after")
    def validate_frozen_diagnostic(self) -> "CounterfactualAudit":
        if self.disposition != "skipped":
            raise ValueError("counterfactual audit requires a skipped opportunity")
        if not self.diagnostic_only:
            raise ValueError("counterfactual result cannot be merged into live state")
        for value in (self.opportunity_id, self.model_sha256, self.config_sha256, self.retained_input_ref):
            if not value.strip():
                raise ValueError("counterfactual identity fields must not be blank")
        if not self.result:
            raise ValueError("counterfactual diagnostic result is required")
        return self

