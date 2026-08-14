from datetime import datetime, timedelta, timezone
import pytest

from sentinel_edge.collaboration import (
    CollaborationConsent,
    CollaborationMetrics,
    CollaborativeCorrelationService,
    CollaborativeSignalEnvelope,
    CorrelationDomain,
    create_signal,
    evaluate_correlation,
    load_policy,
)

NOW = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)
CONSENT = CollaborationConsent(
    sharing_enabled=True,
    research_enabled=False,
    hazards={"earthquake": True, "wildfire": True, "flood": True, "landslide": True},
    policy_version="collab-demo-v1",
    updated_at=NOW,
)


def make_signal(hazard: str, observation: str, domain_kind: str, domain_id: str, node: str, **updates):
    value = create_signal(
        consent=CONSENT,
        hazard=hazard,
        observation=observation,
        domain=CorrelationDomain(kind=domain_kind, id=domain_id),
        node_secret=node,
        episode_key=f"{hazard}-episode",
        source_mode="simulated",
        now=NOW,
    )
    assert value is not None
    return value.model_copy(update=updates)


def envelope(signal, message: str, trust: str = "fixture_qualified", validation_state: str = "admitted"):
    return CollaborativeSignalEnvelope(
        received_at=NOW,
        transport="fixture" if trust == "fixture_qualified" else "email",
        transport_message_id=message,
        transport_trust=trust,
        signal=signal,
        validation_state=validation_state,
        validation_reason_codes=[],
        correlation_id=f"corr-{message}",
    )


def test_policy_covers_exactly_four_hazards_with_hazard_specific_windows():
    policy = load_policy()
    assert set(policy.hazards) == {"wildfire", "earthquake", "flood", "landslide"}
    assert policy.hazards["earthquake"].window_seconds == 10
    assert policy.hazards["wildfire"].window_seconds == 180
    assert policy.hazards["flood"].window_seconds == 600
    assert policy.hazards["landslide"].window_seconds == 600


def test_only_earthquake_fixture_path_may_show_simulated_multi_node_trigger():
    eq = [
        make_signal("earthquake", "local_trigger", "spatial_cell", "cell:demo", "a", clock_uncertainty_band="low"),
        make_signal("earthquake", "local_trigger", "spatial_cell", "cell:demo", "b", clock_uncertainty_band="low"),
    ]
    assert evaluate_correlation(eq, now=NOW).selected_action == "multi_node_trigger_simulated"

    for hazard, observation, kind in (
        ("wildfire", "persistent_smoke", "observation_area"),
        ("flood", "water_rising", "river_reach"),
        ("landslide", "movement_anomaly", "slope"),
    ):
        signals = [
            make_signal(hazard, observation, kind, f"{kind}:demo", "a"),
            make_signal(hazard, observation, kind, f"{kind}:demo", "b"),
        ]
        record = evaluate_correlation(signals, now=NOW)
        assert record.selected_action == "create_review_incident"
        assert record.independent_peer_count == 2


def test_earthquake_unsafe_clock_blocks_simulated_trigger_but_peer_count_remains_visible():
    signals = [
        make_signal("earthquake", "local_trigger", "spatial_cell", "cell:clock", "a", clock_uncertainty_band="high"),
        make_signal("earthquake", "local_trigger", "spatial_cell", "cell:clock", "b", clock_uncertainty_band="low"),
    ]
    record = evaluate_correlation(signals, now=NOW)
    assert record.independent_peer_count == 2
    assert record.selected_action == "no_action"
    assert "CLOCK_UNSAFE" in record.blocking_reasons


def test_email_never_becomes_trusted_multi_node_confirmation():
    signals = [
        make_signal("earthquake", "local_trigger", "spatial_cell", "cell:email", "a", clock_uncertainty_band="low"),
        make_signal("earthquake", "local_trigger", "spatial_cell", "cell:email", "b", clock_uncertainty_band="low"),
    ]
    record = evaluate_correlation(signals, now=NOW, transport_trust="email_unverified")
    assert record.selected_action == "create_review_incident"
    assert "EMAIL_UNVERIFIED_REVIEW_ONLY" in record.positive_reasons


def test_component4_service_is_bounded_idempotent_and_emits_decision_traces():
    service = CollaborativeCorrelationService()
    first = make_signal("earthquake", "local_trigger", "spatial_cell", "cell:service", "a", clock_uncertainty_band="low")
    second = make_signal("earthquake", "local_trigger", "spatial_cell", "cell:service", "b", clock_uncertainty_band="low")
    d1 = service.ingest(envelope(first, "message-1"), now=NOW)
    assert d1.selected_action == "no_action"
    d2 = service.ingest(envelope(second, "message-2"), now=NOW)
    assert d2.selected_action == "multi_node_trigger_simulated"
    assert d2.accepted_signal_ids == [first.signal_id, second.signal_id]
    assert d2.created_or_updated_incident_id.startswith("collab-earthquake-")
    assert len(service.repository.decisions()) == 2
    with pytest.raises(ValueError, match="SIGNAL_DUPLICATE"):
        service.ingest(envelope(second, "message-3"), now=NOW)


def test_context_only_input_cannot_create_incident():
    service = CollaborativeCorrelationService()
    signal = make_signal("wildfire", "persistent_smoke", "observation_area", "area:demo", "a")
    decision = service.ingest(envelope(signal, "context-1", validation_state="context_only"), now=NOW)
    assert decision.selected_action == "context_only"
    assert decision.created_or_updated_incident_id is None


def test_expired_signals_are_purged_from_repository():
    service = CollaborativeCorrelationService()
    signal = make_signal("flood", "water_rising", "river_reach", "reach:demo", "a", expires_at=NOW + timedelta(seconds=1))
    service.ingest(envelope(signal, "exp-1"), now=NOW)
    assert service.repository.purge_expired(NOW + timedelta(seconds=2)) == 1
    assert service.repository.envelopes() == ()


def test_metrics_reject_high_cardinality_labels():
    metrics = CollaborationMetrics()
    metrics.inc("collaboration_inbound_total", validation_state="admitted", transport_trust="fixture_qualified")
    with pytest.raises(ValueError, match="HIGH_CARDINALITY"):
        metrics.inc("collaboration_inbound_total", node_pseudonym="node-secret-ish")
