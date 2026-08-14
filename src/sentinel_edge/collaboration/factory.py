"""Opt-in local signal factory; only derived event-level data leaves the node."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from .models import CollaborationConsent, CollaborativeSignal, CorrelationDomain, Hazard

def create_signal(*, consent: CollaborationConsent, hazard: Hazard, observation: str, domain: CorrelationDomain, node_secret: str, episode_key: str, sequence: int = 0, material: bool = True, source_mode: str = "live", now: datetime | None = None) -> CollaborativeSignal | None:
    if not consent.sharing_enabled or not consent.hazards.get(hazard, False) or not material:
        return None
    now = now or datetime.now(timezone.utc)
    episode_id = sha256((node_secret + ":" + episode_key).encode()).hexdigest()[:32]
    node_pseudonym = sha256((node_secret + ":node").encode()).hexdigest()[:32]
    signal_id = sha256(f"{episode_id}:{sequence}".encode()).hexdigest()[:32]
    return CollaborativeSignal(schema_version="1.0", signal_id=signal_id, episode_id=episode_id, sequence=sequence, node_pseudonym=node_pseudonym, hazard=hazard, observation=observation, correlation_domain=domain, event_time_bucket=now.replace(second=0, microsecond=0), confidence_band="unknown", coverage_band="unknown", sensor_health="unknown", clock_uncertainty_band="unknown", source_mode=source_mode, sharing_policy_version=consent.policy_version, research_use_allowed=consent.research_enabled, expires_at=now + timedelta(minutes=10))
