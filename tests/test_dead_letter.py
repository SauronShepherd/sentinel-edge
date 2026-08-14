import pytest

from sentinel_edge.runtime.dead_letter import DeadLetterStore


def _store() -> DeadLetterStore:
    return DeadLetterStore(max_attempts=3, max_records=2)


def test_dead_letter_preserves_envelope_hash_and_lineage_immutably() -> None:
    store = _store()
    item = store.record(record_id="dl-1", envelope={"type": "command"}, payload=b"payload",
        reason="schema_invalid", attempts=1, validity="rejected", aggregate="incident-1",
        destination="component-4", causation_id="cause-1", correlation_id="corr-1", idempotency_key="idem-1")
    assert item.payload_sha256
    assert store.record(record_id="dl-1", envelope={"changed": True}, payload=b"other",
        reason="other", attempts=2, validity="rejected", aggregate="incident-1",
        destination="component-4", causation_id="cause-1", correlation_id="corr-1", idempotency_key="idem-1") == item


def test_redrive_is_new_attempt_and_requires_current_revalidation() -> None:
    store = _store()
    store.record(record_id="dl-1", envelope={}, payload=b"x", reason="failed", attempts=1,
        validity="rejected", aggregate="a", destination="d", causation_id="c",
        correlation_id="r", idempotency_key="i")
    redrive = store.redrive("dl-1", current_valid=True, target_version=4)
    assert redrive["attempt"] == 2 and redrive["idempotency_key"] == "i"
    with pytest.raises(PermissionError):
        store.redrive("dl-1", current_valid=False, target_version=4)
