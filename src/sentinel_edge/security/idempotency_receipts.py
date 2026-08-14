"""Bounded, privacy-safe idempotency receipts for delayed retries."""
from __future__ import annotations

from dataclasses import dataclass
from time import monotonic


@dataclass(frozen=True)
class IdempotencyReceipt:
    key: str
    payload_digest: str
    result: str
    recorded_at: float


class BoundedIdempotencyReceipts:
    """Retain only recent digests/results; never store the original payload."""

    def __init__(self, *, max_entries: int, replay_window_seconds: float) -> None:
        if max_entries < 1 or replay_window_seconds <= 0:
            raise ValueError("receipt bounds must be positive")
        self.max_entries = max_entries
        self.replay_window_seconds = replay_window_seconds
        self._receipts: dict[str, IdempotencyReceipt] = {}

    def apply(self, *, key: str, payload_digest: str, result: str, now: float | None = None) -> tuple[str, bool]:
        if not key.strip() or not payload_digest.strip():
            raise ValueError("key and payload_digest are required")
        timestamp = monotonic() if now is None else now
        self.expire(now=timestamp)
        existing = self._receipts.get(key)
        if existing is not None:
            if existing.payload_digest != payload_digest:
                raise ValueError("idempotency key conflict")
            return existing.result, True
        self._receipts[key] = IdempotencyReceipt(key, payload_digest, result, timestamp)
        self._trim()
        return result, False

    def expire(self, *, now: float | None = None) -> None:
        timestamp = monotonic() if now is None else now
        cutoff = timestamp - self.replay_window_seconds
        self._receipts = {k: v for k, v in self._receipts.items() if v.recorded_at > cutoff}

    def _trim(self) -> None:
        while len(self._receipts) > self.max_entries:
            oldest = min(self._receipts, key=lambda key: self._receipts[key].recorded_at)
            del self._receipts[oldest]

    def __len__(self) -> int:
        return len(self._receipts)
