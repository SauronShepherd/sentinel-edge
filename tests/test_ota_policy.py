import pytest

from sentinel_edge.update.ota_policy import OtaRetrievalPolicy


def test_automatic_ota_is_not_acceptance_dependency() -> None:
    policy = OtaRetrievalPolicy(enabled=True)
    assert policy.as_metadata() == {
        "automatic_ota_retrieval_enabled": True,
        "acceptance_dependency": False,
        "release_gate_dependency": False,
    }


def test_ota_policy_rejects_gate_dependency() -> None:
    with pytest.raises(ValueError, match="acceptance dependency"):
        OtaRetrievalPolicy(release_gate_dependency=True).validate()
