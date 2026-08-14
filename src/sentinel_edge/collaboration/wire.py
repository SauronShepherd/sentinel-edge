"""Deterministic email wire format and inbound policy validation."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from typing import Literal

from pydantic import ValidationError

from .models import ALLOWED_DOMAIN_KINDS, CollaborativeSignal, OBSERVATIONS

SUBJECT = "Sentinel Collaborative Signal v1"
JSON_CONTENT_TYPE = "application/vnd.sentinel-edge.collaborative-signal+json"
MAX_EMAIL_BYTES = 65536
MAX_JSON_BYTES = 16384
TransportTrust = Literal["fixture_qualified", "email_unverified", "authenticated_peer", "rejected", "unknown"]

REASON_CODES = frozenset({
    "SCHEMA_INVALID", "SCHEMA_VERSION_UNSUPPORTED", "PAYLOAD_TOO_LARGE", "EMAIL_TOO_LARGE",
    "MIME_UNSUPPORTED", "MULTIPLE_SIGNAL_PARTS", "SIGNAL_EXPIRED", "SIGNAL_DUPLICATE",
    "TRANSPORT_MESSAGE_DUPLICATE", "OBSERVATION_UNSUPPORTED", "HAZARD_DOMAIN_MISMATCH",
    "DOMAIN_UNKNOWN", "CLOCK_UNSAFE", "SOURCE_MODE_REPLAYED", "SOURCE_MODE_SIMULATED",
    "PEER_UNTRUSTED", "CONSENT_POLICY_UNSUPPORTED", "INTERNAL_ERROR",
})


@dataclass(frozen=True)
class ValidationDecision:
    accepted: bool
    reason_code: str | None = None
    signal: CollaborativeSignal | None = None


def encode_email(signal: CollaborativeSignal, *, sender: str, recipient: str) -> bytes:
    payload = signal.model_dump(mode="json")
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    if len(body) > MAX_JSON_BYTES:
        raise ValueError("PAYLOAD_TOO_LARGE")
    message = EmailMessage(policy=policy.SMTP)
    message["Subject"] = SUBJECT
    message["From"] = sender
    message["To"] = recipient
    message["X-Sentinel-Schema"] = "collaborative-signal-v1"
    message["X-Sentinel-Signal-ID"] = signal.signal_id
    message.set_content("This message contains a Sentinel Edge collaborative hazard signal.\nIt does not contain raw sensor data and is not an official warning.\nThe machine-readable signal is attached as CollaborativeSignalV1 JSON.\n")
    message.add_attachment(body, maintype="application", subtype="vnd.sentinel-edge.collaborative-signal+json", filename="signal.json")
    encoded = message.as_bytes()
    if len(encoded) > MAX_EMAIL_BYTES:
        raise ValueError("EMAIL_TOO_LARGE")
    return encoded


def decode_signal_email(raw: bytes) -> CollaborativeSignal:
    if len(raw) > MAX_EMAIL_BYTES:
        raise ValueError("EMAIL_TOO_LARGE")
    message = BytesParser(policy=policy.default).parsebytes(raw)
    if message.get("Subject") != SUBJECT:
        raise ValueError("MIME_UNSUPPORTED")
    parts = [part for part in message.walk() if part.get_content_type() == JSON_CONTENT_TYPE]
    if len(parts) != 1:
        raise ValueError("MULTIPLE_SIGNAL_PARTS" if len(parts) > 1 else "MIME_UNSUPPORTED")
    body = parts[0].get_payload(decode=True) or b""
    if len(body) > MAX_JSON_BYTES:
        raise ValueError("PAYLOAD_TOO_LARGE")
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("SCHEMA_INVALID") from exc
    if not isinstance(payload, dict):
        raise ValueError("SCHEMA_INVALID")
    if payload.get("schema_version") != "1.0":
        raise ValueError("SCHEMA_VERSION_UNSUPPORTED")
    hazard = payload.get("hazard")
    observation = payload.get("observation")
    if hazard in OBSERVATIONS and observation not in OBSERVATIONS[hazard]:
        raise ValueError("OBSERVATION_UNSUPPORTED")
    try:
        return CollaborativeSignal.model_validate(payload)
    except (ValidationError, ValueError) as exc:
        raise ValueError("SCHEMA_INVALID") from exc


class CollaborativeInboundValidator:
    def validate(self, *, signal: CollaborativeSignal, received_at: datetime, transport_trust: TransportTrust, seen_signal_ids: set[str] | None = None) -> ValidationDecision:
        seen_signal_ids = seen_signal_ids or set()
        if signal.signal_id in seen_signal_ids:
            return ValidationDecision(False, "SIGNAL_DUPLICATE")
        if signal.schema_version != "1.0":
            return ValidationDecision(False, "SCHEMA_VERSION_UNSUPPORTED")
        if signal.expires_at <= received_at:
            return ValidationDecision(False, "SIGNAL_EXPIRED")
        if signal.source_mode == "replayed":
            return ValidationDecision(False, "SOURCE_MODE_REPLAYED")
        if signal.observation not in OBSERVATIONS[signal.hazard]:
            return ValidationDecision(False, "OBSERVATION_UNSUPPORTED")
        if signal.correlation_domain.kind == "unknown":
            return ValidationDecision(True, "DOMAIN_UNKNOWN", signal)
        if signal.correlation_domain.kind not in ALLOWED_DOMAIN_KINDS[signal.hazard]:
            return ValidationDecision(False, "HAZARD_DOMAIN_MISMATCH")
        if transport_trust in {"unknown", "rejected"}:
            return ValidationDecision(False, "PEER_UNTRUSTED")
        if signal.hazard == "earthquake" and signal.clock_uncertainty_band in {"high", "unknown"}:
            return ValidationDecision(True, "CLOCK_UNSAFE", signal)
        if signal.source_mode == "simulated":
            return ValidationDecision(True, "SOURCE_MODE_SIMULATED", signal)
        return ValidationDecision(True, None, signal)
