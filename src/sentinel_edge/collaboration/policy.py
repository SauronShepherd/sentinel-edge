"""Hazard-specific collaboration policy with explicit trust limitations."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from .models import ALLOWED_DOMAIN_KINDS, CollaborativeSignal

@dataclass(frozen=True)
class CorrelationDecision:
    action: str
    reason_codes: tuple[str, ...]
    independent_peer_count: int
    transport_trust: str

def validate_signal(signal: CollaborativeSignal, *, now: datetime | None = None) -> tuple[str, ...]:
    now = now or datetime.now(timezone.utc)
    reasons: list[str] = []
    if signal.expires_at <= now:
        reasons.append("EXPIRED_SIGNAL")
    if signal.correlation_domain.kind == "unknown":
        reasons.append("UNKNOWN_DOMAIN_CONTEXT_ONLY")
    elif signal.correlation_domain.kind not in ALLOWED_DOMAIN_KINDS[signal.hazard]:
        reasons.append("HAZARD_DOMAIN_MISMATCH")
    if signal.source_mode == "replayed":
        reasons.append("REPLAYED_SIGNAL")
    return tuple(reasons)

def correlate(signals: list[CollaborativeSignal], *, now: datetime | None = None, window: timedelta = timedelta(minutes=5), transport_trust: str = "fixture_qualified") -> CorrelationDecision:
    now = now or datetime.now(timezone.utc)
    admitted = [s for s in signals if not validate_signal(s, now=now) and now - window <= s.event_time_bucket <= now + window]
    peers = {s.node_pseudonym for s in admitted}
    if len(peers) < 2:
        return CorrelationDecision("NO_CORRELATION", ("INSUFFICIENT_INDEPENDENT_PEERS",), len(peers), transport_trust)
    domains = {s.correlation_domain.id for s in admitted if s.correlation_domain.kind != "unknown"}
    if len(domains) != 1:
        return CorrelationDecision("NO_CORRELATION", ("INCOMPATIBLE_CORRELATION_DOMAINS",), len(peers), transport_trust)
    if transport_trust == "email_unverified":
        return CorrelationDecision("REVIEW_REQUIRED", ("EMAIL_UNVERIFIED_TRANSPORT",), len(peers), transport_trust)
    if any(s.hazard == "earthquake" and s.clock_uncertainty_band in {"high", "unknown"} for s in admitted):
        return CorrelationDecision("REVIEW_REQUIRED", ("CLOCK_UNCERTAINTY_BLOCKS_MULTI_NODE",), len(peers), transport_trust)
    return CorrelationDecision("MULTI_NODE_TRIGGER_SIMULATED", ("INDEPENDENT_PEERS_MATCHED",), len(peers), transport_trust)
