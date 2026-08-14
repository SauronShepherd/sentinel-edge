"""Deterministic bounded source resilience: timeout, cache, backoff, circuit breaker."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResilienceDecision:
    allowed: bool
    use_cache: bool
    backoff_seconds: float
    reason: str


class SourceCircuit:
    def __init__(self, *, failure_threshold: int = 3, base_backoff_seconds: float = 1.0) -> None:
        if failure_threshold < 1 or base_backoff_seconds <= 0:
            raise ValueError("invalid circuit policy")
        self.failure_threshold = failure_threshold
        self.base_backoff_seconds = base_backoff_seconds
        self.failures = 0
        self.open = False

    def before_fetch(self, *, cache_available: bool) -> ResilienceDecision:
        if self.open:
            return ResilienceDecision(False, cache_available, self.base_backoff_seconds * self.failures, "circuit_open")
        return ResilienceDecision(True, False, self.base_backoff_seconds * self.failures, "fetch_allowed")

    def record_success(self) -> None:
        self.failures = 0
        self.open = False

    def record_failure(self, *, cache_available: bool) -> ResilienceDecision:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.open = True
        return ResilienceDecision(not self.open, cache_available, self.base_backoff_seconds * self.failures, "circuit_open" if self.open else "retry_backoff")
