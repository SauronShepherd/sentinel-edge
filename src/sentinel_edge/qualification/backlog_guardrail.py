"""Catch-up burst admission below protected Tier A service capacity."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CatchUpBurstDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    backlog_items: int = Field(ge=0)
    requested_rate_per_second: float = Field(ge=0.0)
    tier_a_reserved_rate_per_second: float = Field(gt=0.0)
    admitted_rate_per_second: float = Field(ge=0.0)
    protected_service_preserved: bool
    deferred_items: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_guardrail(self) -> "CatchUpBurstDecision":
        if self.admitted_rate_per_second >= self.tier_a_reserved_rate_per_second:
            raise ValueError("catch-up rate must remain below Tier A reserved capacity")
        if self.deferred_items != max(0, self.backlog_items - int(self.admitted_rate_per_second)):
            raise ValueError("deferred backlog accounting mismatch")
        if not self.protected_service_preserved:
            raise ValueError("protected Tier A service must be preserved")
        return self


def admit_catch_up_burst(*, backlog_items: int, requested_rate_per_second: float,
                         tier_a_reserved_rate_per_second: float) -> CatchUpBurstDecision:
    admitted = min(requested_rate_per_second, max(0.0, tier_a_reserved_rate_per_second - 1.0))
    return CatchUpBurstDecision(backlog_items=backlog_items, requested_rate_per_second=requested_rate_per_second,
        tier_a_reserved_rate_per_second=tier_a_reserved_rate_per_second, admitted_rate_per_second=admitted,
        protected_service_preserved=True, deferred_items=max(0, backlog_items - int(admitted)))
