"""Offline deterministic collaboration demonstration."""
from datetime import datetime, timezone
from .factory import create_signal
from .models import CollaborationConsent, CorrelationDomain
from .policy import correlate

def run_demo() -> dict[str, object]:
    now = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)
    consent = CollaborationConsent(sharing_enabled=True, research_enabled=False, hazards={"earthquake": True, "wildfire": False, "flood": False, "landslide": False}, policy_version="1", updated_at=now)
    domain = CorrelationDomain(kind="spatial_cell", id="cell:demo")
    signals = [create_signal(consent=consent, hazard="earthquake", observation="local_trigger", domain=domain, node_secret=peer, episode_key="demo", source_mode="simulated", now=now).model_copy(update={"clock_uncertainty_band": "low"}) for peer in ("peer-a", "peer-b")]
    decision = correlate([s for s in signals if s is not None], now=now)
    return {"mode": "SIMULATED", "independent_peer_count": decision.independent_peer_count, "action": decision.action, "reason_codes": list(decision.reason_codes), "transport_trust": decision.transport_trust}
