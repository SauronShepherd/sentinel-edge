"""Deployment-readiness card; declares purpose without legal compliance claims."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeploymentGovernanceCard:
    intended_purpose: str
    operator_authority: str
    prohibited_uses: tuple[str, ...]
    jurisdiction: str
    deployment_class: str
    review_completed: bool = False
    legal_conformity_claim: bool = False

    def __post_init__(self) -> None:
        if any(not value.strip() for value in (self.intended_purpose, self.operator_authority, self.jurisdiction, self.deployment_class)) or not self.prohibited_uses:
            raise ValueError("deployment governance card is incomplete")
        if self.legal_conformity_claim:
            raise ValueError("repository cannot declare legal conformity by default")

    @property
    def operational_use_allowed(self) -> bool:
        return self.review_completed


def require_operational_review(card: DeploymentGovernanceCard) -> None:
    if not card.review_completed:
        raise PermissionError("jurisdiction and deployment classification review required")
