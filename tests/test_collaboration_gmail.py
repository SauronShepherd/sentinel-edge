from datetime import datetime, timezone
import asyncio

from sentinel_edge.collaboration.factory import create_signal
from sentinel_edge.collaboration.gmail import GmailCollaborativeSignalConnector, GmailReceiptStore
from sentinel_edge.collaboration.models import CollaborationConsent, CorrelationDomain
from sentinel_edge.collaboration.wire import encode_email


class FakeGmail:
    def __init__(self, raw):
        self.raw = raw
        self.labels = []
    async def list_messages(self, query):
        assert query == 'subject:"Sentinel Collaborative Signal v1" newer_than:7d'
        return [{"id": "gmail-1"}, {"id": "gmail-2"}]
    async def get_message(self, message_id):
        return self.raw if message_id == "gmail-1" else b"bad"
    async def modify_labels(self, message_id, *, add, remove):
        self.labels.append((message_id, tuple(add), tuple(remove)))


def make_signal():
    now = datetime.now(timezone.utc)
    consent = CollaborationConsent(sharing_enabled=True, research_enabled=False, hazards={"wildfire": True, "earthquake": False, "flood": False, "landslide": False}, policy_version="collab-demo-v1", updated_at=now)
    return create_signal(consent=consent, hazard="wildfire", observation="possible_smoke", domain=CorrelationDomain(kind="observation_area", id="area:demo"), node_secret="secret", episode_key="episode")


def test_gmail_poll_emits_component_one_envelope_and_labels_results():
    signal = make_signal()
    fake = FakeGmail(encode_email(signal, sender="a@b.invalid", recipient="c@d.invalid"))
    emitted = []
    connector = GmailCollaborativeSignalConnector(client=fake, emit_envelope=emitted.append, enabled=True)
    assert asyncio.run(connector.validate_config())["valid"]
    async def collect(envelope):
        emitted.append(envelope)
    connector = GmailCollaborativeSignalConnector(client=fake, emit_envelope=collect, enabled=True)
    result = asyncio.run(connector.poll_once(received_at=signal.event_time_bucket))
    assert result.accepted == 1 and result.rejected == 1
    assert emitted[0]["transport_trust"] == "email_unverified"
    assert fake.labels[0][1] == ("sentinel/processed",)
    assert fake.labels[1][1] == ("sentinel/rejected",)


def test_gmail_poll_is_idempotent_and_disabled_is_noop():
    signal = make_signal()
    fake = FakeGmail(encode_email(signal, sender="a@b.invalid", recipient="c@d.invalid"))
    async def noop(_):
        return None
    connector = GmailCollaborativeSignalConnector(client=fake, emit_envelope=noop, enabled=True)
    asyncio.run(connector.poll_once(received_at=signal.event_time_bucket))
    result = asyncio.run(connector.poll_once(received_at=signal.event_time_bucket))
    assert result.duplicate == 2 and result.accepted == 0
    disabled = GmailCollaborativeSignalConnector(client=fake, emit_envelope=noop, enabled=False)
    disabled_result = asyncio.run(disabled.poll_once())
    assert (disabled_result.accepted, disabled_result.rejected, disabled_result.duplicate) == (0, 0, 0)


def test_gmail_poll_has_bounded_inflight_and_deterministic_cursor():
    signal = make_signal()
    fake = FakeGmail(encode_email(signal, sender="a@b.invalid", recipient="c@d.invalid"))
    async def noop(_):
        return None
    connector = GmailCollaborativeSignalConnector(client=fake, emit_envelope=noop, enabled=True, max_inflight=1)
    result = asyncio.run(connector.poll_once(received_at=signal.event_time_bucket))
    assert result.cursor == "gmail-1"
    assert result.heartbeat_at is not None
    assert "MAX_INFLIGHT_BOUNDED" in result.reason_codes
    assert result.accepted == 1 and result.rejected == 0


def test_gmail_receipts_survive_connector_restart(tmp_path):
    signal = make_signal()
    fake = FakeGmail(encode_email(signal, sender="a@b.invalid", recipient="c@d.invalid"))
    async def noop(_):
        return None
    receipt_path = tmp_path / "receipts.json"
    first = GmailCollaborativeSignalConnector(client=fake, emit_envelope=noop, enabled=True, receipt_store=GmailReceiptStore(receipt_path))
    result1 = asyncio.run(first.poll_once(received_at=signal.event_time_bucket))
    assert result1.accepted == 1
    second = GmailCollaborativeSignalConnector(client=fake, emit_envelope=noop, enabled=True, receipt_store=GmailReceiptStore(receipt_path))
    result2 = asyncio.run(second.poll_once(received_at=signal.event_time_bucket))
    assert result2.duplicate == 2
