"""Telemetry cardinality, memory, and privacy-budget evidence."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TelemetryBudgetReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    unique_series: int = Field(ge=0)
    maximum_series: int = Field(gt=0)
    peak_memory_bytes: int = Field(ge=0)
    maximum_memory_bytes: int = Field(gt=0)
    leak_corpus_checked: int = Field(ge=0)
    leak_matches: int = Field(ge=0)
    stress_passed: bool

    @model_validator(mode="after")
    def validate_budget(self) -> "TelemetryBudgetReport":
        if self.unique_series > self.maximum_series:
            raise ValueError("telemetry cardinality budget exceeded")
        if self.peak_memory_bytes > self.maximum_memory_bytes:
            raise ValueError("telemetry memory budget exceeded")
        if self.leak_matches != 0:
            raise ValueError("telemetry leak corpus is not clean")
        if not self.stress_passed:
            raise ValueError("telemetry stress/privacy checks did not pass")
        return self
