import pytest

from sentinel_edge.qualification.root_integrity import RootIntegrityReadiness


def test_unverified_host_cannot_claim_end_to_end_protection() -> None:
    card = RootIntegrityReadiness(False, powered_off_limitation=True, privileged_host_limitation=False).card()
    assert card["end_to_end_protection_claim_allowed"] is False


def test_field_deployment_requires_profile_or_explicit_limitation() -> None:
    with pytest.raises(ValueError, match="qualified root integrity"):
        RootIntegrityReadiness(False, False, False)
