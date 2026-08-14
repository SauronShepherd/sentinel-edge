"""Reproducible CPU execution-path comparison evidence."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CpuExecutionPathComparison(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path_id: str
    build_command: str
    build_log_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    kleidiai_enabled: bool
    control_ablation_retained: bool
    control_log_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    comparison_metrics: dict[str, float]

    @model_validator(mode="after")
    def validate_comparison(self) -> "CpuExecutionPathComparison":
        if not self.path_id.strip() or not self.build_command.strip():
            raise ValueError("path id and exact build command are required")
        if self.kleidiai_enabled is not True:
            raise ValueError("primary record must describe the KleidiAI-enabled path")
        if not self.control_ablation_retained:
            raise ValueError("disabled-control ablation must be retained")
        if not self.comparison_metrics:
            raise ValueError("comparison metrics are required")
        return self
