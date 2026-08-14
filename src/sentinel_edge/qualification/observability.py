"""Diagnostic-ablation measurements for observability overhead."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ObservabilityOverheadReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    baseline_cpu_percent: float = Field(ge=0.0)
    diagnostic_cpu_percent: float = Field(ge=0.0)
    baseline_io_bytes: int = Field(ge=0)
    diagnostic_io_bytes: int = Field(ge=0)
    baseline_latency_ms: float = Field(ge=0.0)
    diagnostic_latency_ms: float = Field(ge=0.0)
    ablation_id: str
    cpu_perturbation_percent: float
    io_perturbation_bytes: int
    latency_perturbation_ms: float

    @model_validator(mode="after")
    def validate_measurement(self) -> "ObservabilityOverheadReport":
        if not self.ablation_id.strip():
            raise ValueError("diagnostic ablation id is required")
        if self.cpu_perturbation_percent != self.diagnostic_cpu_percent - self.baseline_cpu_percent:
            raise ValueError("CPU perturbation does not match measurements")
        if self.io_perturbation_bytes != self.diagnostic_io_bytes - self.baseline_io_bytes:
            raise ValueError("IO perturbation does not match measurements")
        if self.latency_perturbation_ms != self.diagnostic_latency_ms - self.baseline_latency_ms:
            raise ValueError("latency perturbation does not match measurements")
        return self
