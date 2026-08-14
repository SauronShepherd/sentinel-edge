import pytest

from sentinel_edge.qualification.applicability import (
    ApplicabilityDisposition,
    ApplicabilityDomain,
    ApplicabilityEvidence,
    evaluate_applicability,
)


def _domain() -> ApplicabilityDomain:
    return ApplicabilityDomain(frozenset({"site-a"}), frozenset({"camera"}), frozenset({"summer"}), frozenset({"smoke"}), "adjudicated-v1")


def test_exact_target_domain_evidence_allows_claim() -> None:
    result = evaluate_applicability(_domain(), ApplicabilityEvidence("site-a", "camera", "summer", "smoke", "adjudicated-v1"), request_transfer_claim=True)
    assert result.disposition is ApplicabilityDisposition.ALLOW
    assert result.target_domain_evidence is True


def test_unknown_domain_abstains_and_transfer_requires_review() -> None:
    evidence = ApplicabilityEvidence("site-b", "camera", "summer", "smoke", "adjudicated-v1")
    assert evaluate_applicability(_domain(), evidence).disposition is ApplicabilityDisposition.ABSTAIN
    transfer = evaluate_applicability(_domain(), evidence, request_transfer_claim=True)
    assert transfer.disposition is ApplicabilityDisposition.REVIEW_REQUIRED
    assert transfer.target_domain_evidence is False


def test_domain_cannot_omit_dimensions() -> None:
    with pytest.raises(ValueError):
        ApplicabilityDomain(frozenset(), frozenset({"camera"}), frozenset({"summer"}), frozenset({"smoke"}), "labels")
