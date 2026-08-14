"""Security contact, supported versions, and intended support period."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ProductSupportPolicy:
    security_contact: str
    supported_versions: tuple[str, ...]
    support_start: date
    support_end: date
    cra_conformity_claimed: bool = False

    def __post_init__(self) -> None:
        if not self.security_contact.strip() or not self.supported_versions:
            raise ValueError("support policy requires security contact and versions")
        if self.support_end <= self.support_start:
            raise ValueError("support period must be positive")

    def as_security_metadata(self) -> dict[str, object]:
        return {"security_contact": self.security_contact, "supported_versions": list(self.supported_versions), "support_start": self.support_start.isoformat(), "support_end": self.support_end.isoformat(), "cra_conformity_claimed": self.cra_conformity_claimed}
