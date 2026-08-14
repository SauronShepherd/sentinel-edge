import pytest

from sentinel_edge.runtime.media_persistence import MediaPersistenceOutcome


def test_media_failure_preserves_transition_and_marks_evidence_unavailable() -> None:
    outcome = MediaPersistenceOutcome(True, False, None, "evidence-unavailable")
    assert outcome.complete_bundle() is False


def test_dropped_transition_is_rejected() -> None:
    with pytest.raises(ValueError, match="silently dropped"):
        MediaPersistenceOutcome(False, False, None, "degraded")
