from datetime import datetime, timedelta, timezone

from sentinel_edge.collaboration.factory import create_signal
from sentinel_edge.collaboration.models import CollaborationConsent, CorrelationDomain
from sentinel_edge.collaboration.smtp import SmtpEmailCollaborativeSignalPublisher, SmtpQueueConfig


def signal():
    now = datetime.now(timezone.utc)
    consent = CollaborationConsent(sharing_enabled=True, research_enabled=False, hazards={"wildfire": True, "earthquake": False, "flood": False, "landslide": False}, policy_version="collab-demo-v1", updated_at=now)
    return create_signal(consent=consent, hazard="wildfire", observation="possible_smoke", domain=CorrelationDomain(kind="observation_area", id="area:demo"), node_secret="secret", episode_key="episode")


def test_smtp_publisher_sends_and_suppresses_unchanged_updates():
    sent = []
    publisher = SmtpEmailCollaborativeSignalPublisher(sender="node@example.invalid", recipient="inbox@example.invalid", send_bytes=sent.append)
    item = signal()
    assert publisher.publish(item) == "queued"
    assert publisher.drain_once() == "sent"
    assert len(sent) == 1
    assert publisher.publish(item) == "suppressed_unchanged"


def test_smtp_publisher_bounded_retry_and_expiry():
    attempts = []
    def fail(_: bytes):
        attempts.append(1)
        raise OSError("offline")
    publisher = SmtpEmailCollaborativeSignalPublisher(sender="a@b.invalid", recipient="c@d.invalid", send_bytes=fail, config=SmtpQueueConfig(max_attempts=2, initial_backoff_seconds=0, max_backoff_seconds=0))
    assert publisher.publish(signal()) == "queued"
    assert publisher.drain_once() == "retry_scheduled"
    assert publisher.drain_once() == "dead_letter"
    assert len(attempts) == 2


def test_expired_signal_never_enters_queue():
    item = signal().model_copy(update={"expires_at": datetime.now(timezone.utc) - timedelta(seconds=1)})
    publisher = SmtpEmailCollaborativeSignalPublisher(sender="a@b.invalid", recipient="c@d.invalid", send_bytes=lambda _: None)
    assert publisher.publish(item) == "expired"
    assert publisher.queued_items == 0
