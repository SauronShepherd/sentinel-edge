"""Audited workload rate limiting with an uncancellable minimum local cadence."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RateLimitDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    reason: str
    duration_seconds: float = Field(ge=0.0)
    affected_workload: str
    requested_cadence_seconds: float = Field(gt=0.0)
    minimum_local_cadence_seconds: float = Field(gt=0.0)
    effective_cadence_seconds: float = Field(gt=0.0)
    suppressed: bool

    @model_validator(mode="after")
    def validate_decision(self) -> "RateLimitDecision":
        if not self.reason.strip() or not self.affected_workload.strip():
            raise ValueError("rate limit reason and affected workload are required")
        if self.effective_cadence_seconds < self.minimum_local_cadence_seconds:
            raise ValueError("minimum local cadence cannot be suppressed")
        return self


def evaluate_rate_limit(*, reason: str, duration_seconds: float, affected_workload: str,
                        requested_cadence_seconds: float, minimum_local_cadence_seconds: float) -> RateLimitDecision:
    effective = max(requested_cadence_seconds, minimum_local_cadence_seconds)
    return RateLimitDecision(reason=reason, duration_seconds=duration_seconds, affected_workload=affected_workload,
        requested_cadence_seconds=requested_cadence_seconds, minimum_local_cadence_seconds=minimum_local_cadence_seconds,
        effective_cadence_seconds=effective, suppressed=effective > requested_cadence_seconds)
