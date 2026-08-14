from datetime import datetime, timezone

from sentinel_edge.collaboration import CollaborationConsent, CorrelationDomain, FixtureCollaborativeSignalPublisher


def consent(sharing: bool):
    return CollaborationConsent(sharing_enabled=sharing, research_enabled=False, hazards={"wildfire": True, "earthquake": False, "flood": False, "landslide": False}, policy_version="collab-demo-v1", updated_at=datetime.now(timezone.utc))


def test_fixture_publisher_requires_opt_in_and_keeps_derived_signal_only():
    publisher = FixtureCollaborativeSignalPublisher()
    denied = publisher.publish(consent=consent(False), hazard="wildfire", observation="possible_smoke", domain=CorrelationDomain(kind="observation_area", id="area:demo"), node_secret="secret", episode_key="episode")
    assert denied.published is False and publisher.signals == []
    accepted = publisher.publish(consent=consent(True), hazard="wildfire", observation="possible_smoke", domain=CorrelationDomain(kind="observation_area", id="area:demo"), node_secret="secret", episode_key="episode")
    assert accepted.published is True
    assert accepted.signal and accepted.signal.source_mode == "simulated"
    assert not hasattr(accepted.signal, "raw_sensor_data")
