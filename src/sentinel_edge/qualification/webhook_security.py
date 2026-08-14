"""Provider-neutral webhook authenticity and replay controls."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class DeliveryReplayStore:
    """Small deterministic store contract; production callers can persist the set."""

    _delivery_ids: set[str] = field(default_factory=set)

    def claim(self, delivery_id: str) -> bool:
        if not delivery_id.strip() or delivery_id in self._delivery_ids:
            return False
        self._delivery_ids.add(delivery_id)
        return True


@dataclass(frozen=True)
class WebhookDecision:
    accepted: bool
    code: str
    delivery_id: str


@dataclass
class WebhookKeyRing:
    """Bounded rotation window: one current key and at most one grace key."""

    current: bytes
    previous: bytes | None = None
    previous_until: int | None = None

    def rotate(self, new_key: bytes, *, grace_seconds: int, now: int) -> None:
        if not new_key or grace_seconds < 0:
            raise ValueError("new key and non-negative grace are required")
        self.previous = self.current
        self.previous_until = now + grace_seconds
        self.current = new_key

    def candidates(self, *, now: int) -> tuple[bytes, ...]:
        if self.previous is not None and self.previous_until is not None and now <= self.previous_until:
            return (self.current, self.previous)
        self.previous = None
        self.previous_until = None
        return (self.current,)


def verify_hmac_webhook(*, raw_body: bytes, provider: str, delivery_id: str,
                        timestamp: int, now: int, signature: str, secret: bytes,
                        replay_store: DeliveryReplayStore, max_skew_seconds: int = 300,
                        verification_started: int | None = None, max_verification_seconds: int = 5) -> WebhookDecision:
    """Verify provider envelope over raw bytes before semantic parsing."""
    if not provider.strip() or not delivery_id.strip():
        return WebhookDecision(False, "missing_provider_or_delivery_id", delivery_id)
    if len(raw_body) > 1_048_576:
        return WebhookDecision(False, "payload_too_large", delivery_id)
    if verification_started is not None and (max_verification_seconds < 0 or now - verification_started > max_verification_seconds):
        return WebhookDecision(False, "acknowledgement_window_exceeded", delivery_id)
    if max_skew_seconds < 0 or abs(now - timestamp) > max_skew_seconds:
        return WebhookDecision(False, "timestamp_out_of_window", delivery_id)
    if not secret or not signature.startswith("sha256="):
        return WebhookDecision(False, "signature_missing", delivery_id)
    material = f"{timestamp}.".encode() + raw_body
    expected = "sha256=" + hmac.new(secret, material, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return WebhookDecision(False, "signature_invalid", delivery_id)
    if not replay_store.claim(f"{provider}:{delivery_id}"):
        return WebhookDecision(False, "delivery_replayed", delivery_id)
    return WebhookDecision(True, "accepted", delivery_id)


def verify_hmac_webhook_with_keyring(*, raw_body: bytes, provider: str, delivery_id: str,
                                     timestamp: int, now: int, signature: str,
                                     keyring: WebhookKeyRing, replay_store: DeliveryReplayStore,
                                     max_skew_seconds: int = 300) -> WebhookDecision:
    """Verify against the current key and bounded rotation grace key."""
    for secret in keyring.candidates(now=now):
        decision = verify_hmac_webhook(raw_body=raw_body, provider=provider, delivery_id=delivery_id,
            timestamp=timestamp, now=now, signature=signature, secret=secret,
            replay_store=replay_store, max_skew_seconds=max_skew_seconds)
        if decision.accepted or decision.code == "delivery_replayed":
            return decision
    return WebhookDecision(False, "signature_invalid", delivery_id)
