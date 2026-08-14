import hashlib
import hmac

from sentinel_edge.qualification.webhook_security import DeliveryReplayStore, WebhookKeyRing, verify_hmac_webhook, verify_hmac_webhook_with_keyring


def test_raw_bytes_are_verified_before_acceptance_and_replay_is_rejected() -> None:
    body = b'{"event":"report"}'
    secret = b"provider-secret"
    sig = "sha256=" + hmac.new(secret, b"1700000000." + body, hashlib.sha256).hexdigest()
    store = DeliveryReplayStore()
    first = verify_hmac_webhook(raw_body=body, provider="provider", delivery_id="d-1",
        timestamp=1700000000, now=1700000001, signature=sig, secret=secret, replay_store=store)
    second = verify_hmac_webhook(raw_body=body, provider="provider", delivery_id="d-1",
        timestamp=1700000000, now=1700000001, signature=sig, secret=secret, replay_store=store)
    assert first.accepted and first.code == "accepted"
    assert not second.accepted and second.code == "delivery_replayed"


def test_invalid_signature_timestamp_and_size_are_rejected() -> None:
    store = DeliveryReplayStore()
    common = dict(raw_body=b"body", provider="p", delivery_id="d", timestamp=1, now=1000,
                  signature="sha256=bad", secret=b"s", replay_store=store)
    assert verify_hmac_webhook(**common).code == "timestamp_out_of_window"
    common["timestamp"] = 1000
    assert verify_hmac_webhook(**common).code == "signature_invalid"
    common["raw_body"] = b"x" * (1_048_577)
    assert verify_hmac_webhook(**common).code == "payload_too_large"


def test_key_rotation_accepts_bounded_grace_then_rejects_old_key() -> None:
    body = b"rotation"
    ring = WebhookKeyRing(b"old")
    ring.rotate(b"new", grace_seconds=10, now=100)
    sig = "sha256=" + hmac.new(b"old", b"100." + body, hashlib.sha256).hexdigest()
    assert verify_hmac_webhook_with_keyring(raw_body=body, provider="p", delivery_id="d1",
        timestamp=100, now=105, signature=sig, keyring=ring, replay_store=DeliveryReplayStore()).accepted
    sig2 = "sha256=" + hmac.new(b"old", b"100." + body, hashlib.sha256).hexdigest()
    assert verify_hmac_webhook_with_keyring(raw_body=body, provider="p", delivery_id="d2",
        timestamp=100, now=111, signature=sig2, keyring=ring, replay_store=DeliveryReplayStore()).code == "signature_invalid"


def test_network_allowlist_is_not_sender_identity() -> None:
    decision = verify_hmac_webhook(raw_body=b"body", provider="p", delivery_id="allowed-network",
        timestamp=1000, now=1000, signature="sha256=invalid", secret=b"secret",
        replay_store=DeliveryReplayStore())
    assert not decision.accepted
    assert decision.code == "signature_invalid"


def test_webhook_verification_has_bounded_acknowledgement_window() -> None:
    body = b"body"
    secret = b"secret"
    sig = "sha256=" + hmac.new(secret, b"1000." + body, hashlib.sha256).hexdigest()
    decision = verify_hmac_webhook(raw_body=body, provider="p", delivery_id="ack-1", timestamp=1000, now=1007,
        signature=sig, secret=secret, replay_store=DeliveryReplayStore(), verification_started=1000,
        max_verification_seconds=5)
    assert not decision.accepted and decision.code == "acknowledgement_window_exceeded"
