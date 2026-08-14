"""Opt-in SMTP publisher with a bounded, deterministic retry queue.

The module never stores credentials; callers provide a sender port resolved by
the deployment secret manager. It is experimental H1 functionality.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from random import Random
from typing import Callable

from .models import CollaborativeSignal
from .wire import encode_email


@dataclass(frozen=True)
class SmtpQueueConfig:
    max_items: int = 64
    max_age_seconds: int = 3600
    initial_backoff_seconds: float = 5.0
    max_backoff_seconds: float = 300.0
    max_attempts: int = 8
    ordinary_update_min_interval_seconds: float = 60.0


@dataclass
class QueuedEmail:
    signal: CollaborativeSignal
    raw: bytes
    enqueued_at: datetime
    next_attempt_at: datetime
    attempts: int = 0


class SmtpEmailCollaborativeSignalPublisher:
    def __init__(self, *, sender: str, recipient: str, send_bytes: Callable[[bytes], None], config: SmtpQueueConfig | None = None, random_seed: int = 0) -> None:
        self.sender = sender
        self.recipient = recipient
        self._send_bytes = send_bytes
        self.config = config or SmtpQueueConfig()
        self._random = Random(random_seed)
        self._queue: list[QueuedEmail] = []
        self._sent_by_episode: dict[str, tuple[str, datetime]] = {}

    @property
    def queued_items(self) -> int:
        return len(self._queue)

    @staticmethod
    def _semantic_fingerprint(signal: CollaborativeSignal) -> str:
        import json
        from hashlib import sha256

        payload = signal.model_dump(
            mode="json",
            exclude={"signal_id", "sequence", "event_time_bucket", "expires_at", "reason_codes"},
        )
        return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def publish(self, signal: CollaborativeSignal, *, now: datetime | None = None) -> str:
        now = now or datetime.now(timezone.utc)
        if signal.expires_at <= now:
            return "expired"
        fingerprint = self._semantic_fingerprint(signal)
        previous = self._sent_by_episode.get(signal.episode_id)
        if previous and previous[0] == fingerprint and (now - previous[1]).total_seconds() < self.config.ordinary_update_min_interval_seconds:
            return "suppressed_unchanged"
        for queued in self._queue:
            if queued.signal.episode_id == signal.episode_id and self._semantic_fingerprint(queued.signal) == fingerprint:
                return "suppressed_unchanged"
        raw = encode_email(signal, sender=self.sender, recipient=self.recipient)
        if len(self._queue) >= self.config.max_items:
            return "queue_full"
        self._queue.append(QueuedEmail(signal, raw, now, now))
        return "queued"

    def drain_once(self, *, now: datetime | None = None) -> str:
        now = now or datetime.now(timezone.utc)
        if not self._queue:
            return "empty"
        item = self._queue[0]
        if now < item.next_attempt_at:
            return "not_due"
        if item.signal.expires_at <= now or (now - item.enqueued_at).total_seconds() > self.config.max_age_seconds:
            self._queue.pop(0)
            return "expired"
        try:
            self._send_bytes(item.raw)
        except Exception:
            item.attempts += 1
            if item.attempts >= self.config.max_attempts:
                self._queue.pop(0)
                return "dead_letter"
            delay = min(self.config.max_backoff_seconds, self.config.initial_backoff_seconds * (2 ** (item.attempts - 1)))
            jitter = delay * 0.1 * self._random.random()
            item.next_attempt_at = now + timedelta(seconds=delay + jitter)
            return "retry_scheduled"
        self._queue.pop(0)
        self._sent_by_episode[item.signal.episode_id] = (self._semantic_fingerprint(item.signal), now)
        return "sent"
