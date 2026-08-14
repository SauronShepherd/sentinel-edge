import pytest

from sentinel_edge.security.idempotency_receipts import BoundedIdempotencyReceipts


def test_delayed_retry_replays_once_and_does_not_store_payload() -> None:
    receipts = BoundedIdempotencyReceipts(max_entries=2, replay_window_seconds=10)
    assert receipts.apply(key="k1", payload_digest="d1", result="ok", now=0) == ("ok", False)
    assert receipts.apply(key="k1", payload_digest="d1", result="different", now=5) == ("ok", True)
    assert len(receipts) == 1


def test_receipts_are_bounded_and_expire() -> None:
    receipts = BoundedIdempotencyReceipts(max_entries=2, replay_window_seconds=10)
    receipts.apply(key="k1", payload_digest="d1", result="1", now=0)
    receipts.apply(key="k2", payload_digest="d2", result="2", now=1)
    receipts.apply(key="k3", payload_digest="d3", result="3", now=2)
    assert len(receipts) == 2
    receipts.expire(now=13)
    assert len(receipts) == 0


def test_reusing_key_with_different_digest_is_rejected() -> None:
    receipts = BoundedIdempotencyReceipts(max_entries=2, replay_window_seconds=10)
    receipts.apply(key="k1", payload_digest="d1", result="ok", now=0)
    with pytest.raises(ValueError, match="conflict"):
        receipts.apply(key="k1", payload_digest="d2", result="bad", now=1)
