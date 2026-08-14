import pytest

from sentinel_edge.benchmark.claim_access import ClaimSetAccess


def test_claim_set_access_is_purpose_bound_and_auditable() -> None:
    receipt = ClaimSetAccess("claims-v1", "confirmatory-review", "judge", "audit-1").receipt()
    assert receipt["purpose_bound"] is True
    assert receipt["auditable"] is True


def test_unbound_claim_access_is_rejected() -> None:
    with pytest.raises(ValueError, match="purpose-bound"):
        ClaimSetAccess("claims-v1", "", "judge", "audit-1")
