"""Deterministic validation for cross-component boundary messages."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sentinel_edge.security import canonical_json_bytes, sha256_bytes


@dataclass(frozen=True)
class WireMessage:
    contract: str
    payload_type: str
    delivery_class: str
    producer_component: str
    producer_identity: str
    idempotency_key: str
    aggregate_key: str
    aggregate_version: int
    producer_sequence: int
    payload_length: int
    payload_sha256: str
    payload: dict[str, Any]
    correlation_id: str | None = None
    causation_id: str | None = None


class WireBoundaryPolicy:
    """Validate before deserializing or dispatching a cross-component payload."""

    _DELIVERY = {"critical_state", "replayable_compute", "replace_latest", "telemetry"}

    def __init__(self, *, allowed: dict[str, dict[str, set[str]]], contract_major: int = 1) -> None:
        self.allowed = allowed
        self.contract_major = contract_major

    def validate_raw(self, raw: bytes) -> WireMessage:
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("wire_payload_invalid_encoding") from exc
        if not isinstance(data, dict):
            raise ValueError("wire_envelope_required")
        contract = str(data.get("contract", ""))
        try:
            major = int(contract.split(".", 1)[0])
        except (ValueError, IndexError):
            raise ValueError("wire_contract_invalid")
        if major != self.contract_major:
            raise ValueError("wire_contract_major_unsupported")
        payload = data.get("payload")
        if not isinstance(payload, dict):
            raise ValueError("wire_payload_type_invalid")
        required = ("payload_type", "delivery_class", "producer_component", "producer_identity", "idempotency_key", "aggregate_key", "aggregate_version", "producer_sequence", "payload_length", "payload_sha256")
        if any(not str(data.get(key, "")).strip() for key in required[:6]) or any(key not in data for key in required[6:]):
            raise ValueError("wire_envelope_fields_missing")
        payload_bytes = canonical_json_bytes(payload)
        if int(data["payload_length"]) != len(payload_bytes):
            raise ValueError("wire_payload_length_mismatch")
        if str(data["payload_sha256"]) != sha256_bytes(payload_bytes):
            raise ValueError("wire_payload_digest_mismatch")
        component = str(data["producer_component"])
        payload_type = str(data["payload_type"])
        if payload_type not in self.allowed.get(component, {}):
            raise ValueError("wire_producer_payload_not_allowed")
        if str(data["delivery_class"]) not in self._DELIVERY:
            raise ValueError("wire_delivery_class_unknown")
        if str(data["delivery_class"]) not in self.allowed[component][payload_type]:
            raise ValueError("wire_delivery_class_not_allowed")
        try:
            return WireMessage(**{key: data[key] for key in WireMessage.__dataclass_fields__})
        except (TypeError, ValueError) as exc:
            raise ValueError("wire_envelope_fields_invalid") from exc

    def encode(self, *, contract: str, payload_type: str, delivery_class: str, producer_component: str, producer_identity: str, idempotency_key: str, aggregate_key: str, aggregate_version: int, producer_sequence: int, payload: dict[str, Any], correlation_id: str | None = None, causation_id: str | None = None) -> bytes:
        payload_bytes = canonical_json_bytes(payload)
        return canonical_json_bytes({"contract": contract, "payload_type": payload_type, "delivery_class": delivery_class, "producer_component": producer_component, "producer_identity": producer_identity, "idempotency_key": idempotency_key, "aggregate_key": aggregate_key, "aggregate_version": aggregate_version, "producer_sequence": producer_sequence, "payload_length": len(payload_bytes), "payload_sha256": sha256_bytes(payload_bytes), "payload": payload, "correlation_id": correlation_id, "causation_id": causation_id})
