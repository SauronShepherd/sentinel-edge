from datetime import timedelta

import pytest

from sentinel_edge.collaboration.factory import create_signal
from sentinel_edge.collaboration.models import CollaborationConsent, CorrelationDomain
from sentinel_edge.collaboration.wire import CollaborativeInboundValidator, decode_signal_email, encode_email


def make_signal():
    consent = CollaborationConsent(sharing_enabled=True, research_enabled=False, hazards={"wildfire": True, "earthquake": False, "flood": False, "landslide": False}, policy_version="collab-demo-v1", updated_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc))
    return create_signal(consent=consent, hazard="wildfire", observation="possible_smoke", domain=CorrelationDomain(kind="observation_area", id="area:demo"), node_secret="secret", episode_key="episode")


def test_wire_round_trip_and_human_text_is_not_semantic():
    signal = make_signal()
    raw = encode_email(signal, sender="node@example.invalid", recipient="inbox@example.invalid")
    decoded = decode_signal_email(raw)
    assert decoded == signal


def test_inbound_validator_rejects_replay_and_expiry():
    signal = make_signal()
    validator = CollaborativeInboundValidator()
    assert validator.validate(signal=signal, received_at=signal.event_time_bucket, transport_trust="email_unverified").accepted
    assert validator.validate(signal=signal, received_at=signal.event_time_bucket, transport_trust="email_unverified", seen_signal_ids={signal.signal_id}).reason_code == "SIGNAL_DUPLICATE"
    expired = signal.model_copy(update={"expires_at": signal.event_time_bucket - timedelta(seconds=1)})
    assert validator.validate(signal=expired, received_at=signal.event_time_bucket, transport_trust="email_unverified").reason_code == "SIGNAL_EXPIRED"


def test_wire_rejects_oversized_or_wrong_subject():
    signal = make_signal()
    raw = encode_email(signal, sender="a@b.invalid", recipient="c@d.invalid")
    assert len(raw) < 65536
    with pytest.raises(ValueError, match="MIME_UNSUPPORTED"):
        decode_signal_email(raw.replace(b"Sentinel Collaborative Signal v1", b"Other"))
