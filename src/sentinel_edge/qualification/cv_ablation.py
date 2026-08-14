"""Complete-pipeline computer-vision ablation evidence with explicit fallback."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CvAblationReport:
    target: str
    accelerated_enabled: bool
    preprocessing: str
    inference: str
    postprocessing: str
    fallback_used: bool
    external_benchmark_inherited: bool = False

    def __post_init__(self) -> None:
        if not self.target.strip() or not all(value.strip() for value in (self.preprocessing, self.inference, self.postprocessing)):
            raise ValueError("complete-pipeline CV stages are required")
        if self.external_benchmark_inherited:
            raise ValueError("external benchmark value cannot be inherited")

    def complete_pipeline_effect(self) -> dict[str, object]:
        return {"target": self.target, "accelerated_enabled": self.accelerated_enabled, "stages": [self.preprocessing, self.inference, self.postprocessing], "fallback_used": self.fallback_used, "external_benchmark_inherited": False}
