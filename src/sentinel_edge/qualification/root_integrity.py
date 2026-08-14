"""Deployment-readiness boundary for boot/root-integrity evidence."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RootIntegrityReadiness:
    qualified_boot_profile: bool
    powered_off_limitation: bool
    privileged_host_limitation: bool

    def __post_init__(self) -> None:
        if not (self.qualified_boot_profile or self.powered_off_limitation or self.privileged_host_limitation):
            raise ValueError("field deployment requires qualified root integrity or explicit limitation")

    @property
    def end_to_end_protection_claim_allowed(self) -> bool:
        return self.qualified_boot_profile

    def card(self) -> dict[str, bool]:
        return {"qualified_boot_profile": self.qualified_boot_profile, "powered_off_limitation": self.powered_off_limitation, "privileged_host_limitation": self.privileged_host_limitation, "end_to_end_protection_claim_allowed": self.end_to_end_protection_claim_allowed}
