"""Offline fixture publisher for deterministic collaboration development."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .factory import create_signal
from .models import CollaborationConsent, CollaborativeSignal, CorrelationDomain, Hazard


@dataclass(frozen=True)
class FixturePublishResult:
    published: bool
    signal: CollaborativeSignal | None
    reason: str


class FixtureCollaborativeSignalPublisher:
    """Collects normalized signals in memory; never sends or mutates incidents."""

    def __init__(self) -> None:
        self.signals: list[CollaborativeSignal] = []

    def publish(self, *, consent: CollaborationConsent, hazard: Hazard, observation: str, domain: CorrelationDomain, node_secret: str, episode_key: str, sequence: int = 0, material: bool = True, source_mode: str = "simulated", now: datetime | None = None) -> FixturePublishResult:
        signal = create_signal(consent=consent, hazard=hazard, observation=observation, domain=domain, node_secret=node_secret, episode_key=episode_key, sequence=sequence, material=material, source_mode=source_mode, now=now)
        if signal is None:
            return FixturePublishResult(False, None, "CONSENT_OR_MATERIALITY_DENIED")
        self.signals.append(signal)
        return FixturePublishResult(True, signal, "PUBLISHED_TO_FIXTURE")
