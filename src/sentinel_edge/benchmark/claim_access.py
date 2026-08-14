"""Purpose-bound, auditable access to sealed benchmark claim sets."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClaimSetAccess:
    claim_set_id: str
    purpose: str
    actor: str
    audit_event_id: str

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.claim_set_id, self.purpose, self.actor, self.audit_event_id)):
            raise ValueError("claim-set access requires purpose-bound audit fields")

    def receipt(self) -> dict[str, str | bool]:
        return {"claim_set_id": self.claim_set_id, "purpose": self.purpose, "actor": self.actor, "audit_event_id": self.audit_event_id, "purpose_bound": True, "auditable": True}
