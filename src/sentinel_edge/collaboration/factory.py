"""Opt-in local collaborative signal factory.

Only material event/state transitions are converted to privacy-transformed
CollaborativeSignalV1 records.  Continuous sensor values are never published.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac

from .models import CollaborationConsent, CollaborativeSignal, CorrelationDomain, Hazard
from .privacy import CollaborationPrivacyTransformer


MATERIAL_STATES: dict[str, frozenset[str]] = {
    "earthquake": frozenset({"local_trigger", "earthquake_like_signal", "shaking_ended"}),
    "wildfire": frozenset({"possible_smoke", "persistent_smoke", "smoke_observation_resolved"}),
    "flood": frozenset({"water_rising", "threshold_approaching", "threshold_exceeded", "flooding_observed", "falling"}),
    "landslide": frozenset({"movement_anomaly", "review_required", "movement_observation_resolved"}),
}
_EXPIRY_SECONDS = {"earthquake": 60, "wildfire": 600, "flood": 1800, "landslide": 1800}


class CollaborativeSignalFactory:
    """Stateful v1 factory implementing consent, materiality and sequencing."""

    def __init__(
        self,
        *,
        enabled: bool,
        consent: CollaborationConsent,
        privacy: CollaborationPrivacyTransformer,
        node_identity_ref: str,
        derivation_secret: str,
    ) -> None:
        if not derivation_secret:
            raise ValueError("COLLABORATION_DERIVATION_SECRET_REQUIRED")
        self.enabled = enabled
        self.consent = consent
        self.privacy = privacy
        self.node_identity_ref = node_identity_ref
        self._key = derivation_secret.encode("utf-8")
        self._episodes: dict[tuple[str, str], str] = {}
        self._sequences: dict[str, int] = {}

    def _opaque(self, namespace: str, value: str, length: int = 32) -> str:
        return hmac.new(self._key, f"{namespace}:{value}".encode("utf-8"), "sha256").hexdigest()[:length]

    def build_from_local_event(
        self,
        *,
        hazard: Hazard,
        local_event_ref: str,
        local_state: str,
        local_event_time: datetime,
        local_location_ref: str | None,
        confidence_band: str,
        coverage_band: str,
        sensor_health: str,
        clock_uncertainty_band: str,
        source_mode: str,
        local_sensor_context_ref: str | None = None,
    ) -> CollaborativeSignal | None:
        hazard_name = str(hazard)
        if not self.enabled or not self.consent.sharing_enabled:
            return None
        if not self.consent.hazards.get(hazard, False):
            return None
        if local_state not in MATERIAL_STATES[hazard_name]:
            return None
        if not local_event_ref:
            raise ValueError("LOCAL_EVENT_REF_REQUIRED")
        if local_event_time.tzinfo is None:
            raise ValueError("EVENT_TIME_TIMEZONE_REQUIRED")

        episode_key = (hazard_name, local_event_ref)
        episode_id = self._episodes.setdefault(
            episode_key,
            self._opaque("episode", f"{hazard_name}:{local_event_ref}"),
        )
        sequence = self._sequences.get(episode_id, 0)
        self._sequences[episode_id] = sequence + 1
        domain = self.privacy.derive_domain(
            hazard=hazard,
            local_location_ref=local_location_ref,
            local_sensor_context_ref=local_sensor_context_ref,
        )
        event_bucket = self.privacy.bucket_time(hazard=hazard, event_time=local_event_time)
        signal_id = self._opaque("signal", f"{episode_id}:{sequence}:{local_state}")
        return CollaborativeSignal(
            schema_version="1.0",
            signal_id=signal_id,
            episode_id=episode_id,
            sequence=sequence,
            node_pseudonym=self.privacy.pseudonymize_node(self.node_identity_ref),
            hazard=hazard,
            observation=local_state,
            correlation_domain=domain,
            event_time_bucket=event_bucket,
            confidence_band=confidence_band,
            coverage_band=coverage_band,
            sensor_health=sensor_health,
            clock_uncertainty_band=clock_uncertainty_band,
            source_mode=source_mode,
            sharing_policy_version=self.consent.policy_version,
            research_use_allowed=self.consent.research_enabled,
            expires_at=local_event_time.astimezone(timezone.utc) + timedelta(seconds=_EXPIRY_SECONDS[hazard_name]),
        )


def create_signal(*, consent: CollaborationConsent, hazard: Hazard, observation: str, domain: CorrelationDomain, node_secret: str, episode_key: str, sequence: int = 0, material: bool = True, source_mode: str = "live", now: datetime | None = None) -> CollaborativeSignal | None:
    """Backward-compatible deterministic helper used by existing fixtures."""
    if not consent.sharing_enabled or not consent.hazards.get(hazard, False) or not material:
        return None
    now = now or datetime.now(timezone.utc)
    episode_id = sha256((node_secret + ":" + episode_key).encode()).hexdigest()[:32]
    node_pseudonym = sha256((node_secret + ":node").encode()).hexdigest()[:32]
    signal_id = sha256(f"{episode_id}:{sequence}".encode()).hexdigest()[:32]
    return CollaborativeSignal(schema_version="1.0", signal_id=signal_id, episode_id=episode_id, sequence=sequence, node_pseudonym=node_pseudonym, hazard=hazard, observation=observation, correlation_domain=domain, event_time_bucket=now.replace(second=0, microsecond=0), confidence_band="unknown", coverage_band="unknown", sensor_health="unknown", clock_uncertainty_band="unknown", source_mode=source_mode, sharing_policy_version=consent.policy_version, research_use_allowed=consent.research_enabled, expires_at=now + timedelta(minutes=10))
