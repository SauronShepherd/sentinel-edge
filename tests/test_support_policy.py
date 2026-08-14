from datetime import date

import pytest

from sentinel_edge.release.support_policy import ProductSupportPolicy


def test_support_policy_exposes_contact_versions_and_period_without_cra_claim() -> None:
    policy = ProductSupportPolicy("security@example.invalid", ("1.0",), date(2026, 1, 1), date(2027, 1, 1))
    assert policy.as_security_metadata()["support_end"] == "2027-01-01"
    assert policy.cra_conformity_claimed is False


def test_support_policy_rejects_empty_versions_or_invalid_period() -> None:
    with pytest.raises(ValueError):
        ProductSupportPolicy("security", (), date(2026, 1, 1), date(2027, 1, 1))
    with pytest.raises(ValueError, match="positive"):
        ProductSupportPolicy("security", ("1",), date(2026, 1, 1), date(2026, 1, 1))
