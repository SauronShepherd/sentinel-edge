from datetime import datetime, timedelta, timezone
from sentinel_edge.collaboration import CollaborationConsent, CorrelationDomain, create_signal, correlate, run_demo

NOW = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)
CONSENT = CollaborationConsent(sharing_enabled=True, research_enabled=False, hazards={"earthquake": True, "wildfire": True, "flood": True, "landslide": True}, policy_version="1", updated_at=NOW)

def signal(node, **overrides):
    value = create_signal(consent=CONSENT, hazard="earthquake", observation="local_trigger", domain=CorrelationDomain(kind="spatial_cell", id="cell:coarse-1"), node_secret=node, episode_key="episode", now=NOW)
    assert value is not None
    return value.model_copy(update=overrides)

def test_disabled_consent_emits_no_signal():
    disabled = CONSENT.model_copy(update={"sharing_enabled": False})
    assert create_signal(consent=disabled, hazard="earthquake", observation="local_trigger", domain=CorrelationDomain(kind="spatial_cell", id="cell:coarse-1"), node_secret="secret", episode_key="episode", now=NOW) is None

def test_factory_does_not_share_secret_or_exact_location():
    value = signal("private-hardware-secret")
    dumped = value.model_dump_json()
    assert "private-hardware-secret" not in dumped
    assert "latitude" not in dumped and "longitude" not in dumped
    assert value.research_use_allowed is False

def test_same_peer_messages_count_once():
    decision = correlate([signal("a"), signal("a", sequence=1)], now=NOW)
    assert decision.independent_peer_count == 1
    assert decision.action == "NO_CORRELATION"

def test_two_fixture_peers_can_trigger_simulated_correlation():
    decision = correlate([signal("a", clock_uncertainty_band="low"), signal("b", clock_uncertainty_band="low")], now=NOW)
    assert decision.action == "MULTI_NODE_TRIGGER_SIMULATED"
    assert decision.transport_trust == "fixture_qualified"

def test_email_unverified_peers_only_create_review():
    decision = correlate([signal("a", clock_uncertainty_band="low"), signal("b", clock_uncertainty_band="low")], now=NOW, transport_trust="email_unverified")
    assert decision.action == "REVIEW_REQUIRED"

def test_expired_signal_cannot_create_fresh_decision():
    decision = correlate([signal("a", expires_at=NOW - timedelta(seconds=1)), signal("b")], now=NOW)
    assert decision.action == "NO_CORRELATION"

def test_offline_demo_is_simulated_and_deterministic():
    assert run_demo() == {"mode": "SIMULATED", "independent_peer_count": 2, "action": "MULTI_NODE_TRIGGER_SIMULATED", "reason_codes": ["INDEPENDENT_PEERS_MATCHED"], "transport_trust": "fixture_qualified"}
