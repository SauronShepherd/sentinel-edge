"""Host variability and isolation-ablation evidence contracts."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HostVariabilityReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    boot_to_boot_ms: tuple[float, ...]
    block_to_block_ms: tuple[float, ...]
    paired_blocks: int = Field(ge=1)
    host_noise_findings: tuple[str, ...]

    @model_validator(mode="after")
    def validate_report(self) -> "HostVariabilityReport":
        if not self.boot_to_boot_ms or not self.block_to_block_ms:
            raise ValueError("boot and block variability samples are required")
        if self.paired_blocks > len(self.block_to_block_ms):
            raise ValueError("paired block count exceeds block samples")
        if not self.host_noise_findings:
            raise ValueError("host-noise findings are required")
        return self


class IsolationAblationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    profile_id: str
    measured_before: bool
    control_ablation_retained: bool
    pinned_processes: tuple[str, ...] = ()
    pinned_irqs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_evidence(self) -> "IsolationAblationEvidence":
        if not self.profile_id.strip():
            raise ValueError("isolation profile id is required")
        if (self.pinned_processes or self.pinned_irqs) and not self.measured_before:
            raise ValueError("pinning requires measured-before evidence")
        if not self.control_ablation_retained:
            raise ValueError("control ablation must be retained")
        return self
