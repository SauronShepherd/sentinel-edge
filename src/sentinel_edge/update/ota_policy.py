"""Optional OTA retrieval boundary; never an acceptance or release-gate dependency."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OtaRetrievalPolicy:
    enabled: bool = False
    acceptance_dependency: bool = False
    release_gate_dependency: bool = False

    def validate(self) -> None:
        if self.acceptance_dependency or self.release_gate_dependency:
            raise ValueError("automatic OTA retrieval cannot be an acceptance dependency")

    def as_metadata(self) -> dict[str, bool]:
        self.validate()
        return {
            "automatic_ota_retrieval_enabled": self.enabled,
            "acceptance_dependency": False,
            "release_gate_dependency": False,
        }
