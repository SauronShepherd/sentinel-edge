import pytest

from sentinel_edge.evidence.registry_binding import EvidenceBindingState, EvidenceTarget, bind_evidence


def _target() -> EvidenceTarget:
    return EvidenceTarget("incident_evidence", "ev-1", "content-v1", "a" * 64)


def test_valid_typed_target_binds_and_missing_target_is_distinct() -> None:
    assert bind_evidence("e1", _target()).state is EvidenceBindingState.BOUND
    assert bind_evidence("e2", None).state is EvidenceBindingState.UNBOUND_TARGET


def test_unavailable_states_are_not_flattened_into_verified() -> None:
    assert bind_evidence("e1", _target(), digest_profile_known=False).state is EvidenceBindingState.DIGEST_PROFILE_UNKNOWN
    assert bind_evidence("e2", _target(), content_available=False).state is EvidenceBindingState.CONTENT_UNAVAILABLE
    assert bind_evidence("e3", _target(), later_redacted=True).state is EvidenceBindingState.LATER_REDACTED


def test_missing_digest_profile_is_explicitly_unverified() -> None:
    assert bind_evidence("e1", EvidenceTarget("kind", "id", None, "a" * 64)).state is EvidenceBindingState.DIGEST_PROFILE_UNKNOWN
