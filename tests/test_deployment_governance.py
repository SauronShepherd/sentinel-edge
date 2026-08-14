import pytest

from sentinel_edge.release.deployment_governance import DeploymentGovernanceCard, require_operational_review


def card(reviewed: bool = False) -> DeploymentGovernanceCard:
    return DeploymentGovernanceCard("supervised hazard context", "designated operator", ("autonomous warning", "law-enforcement surveillance"), "jurisdiction-x", "field-lab", reviewed)


def test_governance_card_requires_review_before_operational_use() -> None:
    assert card().operational_use_allowed is False
    with pytest.raises(PermissionError):
        require_operational_review(card())
    require_operational_review(card(True))


def test_legal_conformity_claim_is_rejected() -> None:
    with pytest.raises(ValueError, match="legal conformity"):
        DeploymentGovernanceCard("purpose", "operator", ("prohibited",), "jurisdiction", "research", legal_conformity_claim=True)
