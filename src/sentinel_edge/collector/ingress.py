"""Bounded MQTT/HTTP/WebSocket ingress into the Component-1 observation contract."""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from sentinel_edge.domain.models import Observation, SourceMode


class IngressTransport(StrEnum):
    MQTT = "mqtt"
    HTTP = "http"
    WEBSOCKET = "websocket"


class IngressMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    transport: IngressTransport
    source_id: str
    payload_bytes: int = Field(ge=1)
    observation: Observation
    topic: str | None = None


class IngressRejected(ValueError):
    """Raised before an ingress payload can reach the collector queue."""


def _json_payload(payload: bytes | str | dict[str, Any], *, max_bytes: int) -> dict[str, Any]:
    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive")
    if isinstance(payload, dict):
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    elif isinstance(payload, str):
        raw = payload.encode("utf-8")
    elif isinstance(payload, bytes):
        raw = payload
    else:
        raise IngressRejected("ingress payload must be JSON bytes, text, or an object")
    if not raw or len(raw) > max_bytes:
        raise IngressRejected("ingress payload exceeds configured byte bound")
    try:
        value = json.loads(raw.decode("utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise IngressRejected("ingress payload is not finite JSON") from exc
    if not isinstance(value, dict):
        raise IngressRejected("ingress payload must be a JSON object")
    return value


def normalize_ingress(
    payload: bytes | str | dict[str, Any],
    *,
    transport: IngressTransport,
    source_id: str,
    topic: str | None = None,
    max_bytes: int = 256 * 1024,
) -> IngressMessage:
    """Normalize all supported live transports through one observation contract."""
    if not source_id.strip():
        raise IngressRejected("source_id must not be blank")
    if transport is IngressTransport.MQTT and not (topic and topic.strip()):
        raise IngressRejected("MQTT ingress requires a non-blank topic")
    value = _json_payload(payload, max_bytes=max_bytes)
    nested = value.get("observation", value)
    if not isinstance(nested, dict):
        raise IngressRejected("observation payload must be a JSON object")
    try:
        observation = Observation.model_validate({
            **nested,
            "source_id": source_id,
            "source_mode": SourceMode.LIVE,
            "source_lineage": f"ingress:{transport.value}",
        })
    except Exception as exc:
        raise IngressRejected("ingress payload failed normalized observation validation") from exc
    raw_size = len(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8"))
    return IngressMessage(transport=transport, source_id=source_id, payload_bytes=raw_size, observation=observation, topic=topic)


class HttpIngressAdapter:
    def __init__(self, *, max_bytes: int = 256 * 1024) -> None:
        self.max_bytes = max_bytes

    def accept(self, body: bytes | str | dict[str, Any], *, source_id: str, content_type: str = "application/json") -> IngressMessage:
        if content_type.split(";", 1)[0].strip().lower() != "application/json":
            raise IngressRejected("HTTP ingress requires application/json")
        return normalize_ingress(body, transport=IngressTransport.HTTP, source_id=source_id, max_bytes=self.max_bytes)


class WebSocketIngressAdapter:
    def __init__(self, *, max_bytes: int = 256 * 1024) -> None:
        self.max_bytes = max_bytes

    def accept(self, message: bytes | str | dict[str, Any], *, source_id: str) -> IngressMessage:
        return normalize_ingress(message, transport=IngressTransport.WEBSOCKET, source_id=source_id, max_bytes=self.max_bytes)


class MqttIngressAdapter:
    def __init__(self, *, max_bytes: int = 256 * 1024) -> None:
        self.max_bytes = max_bytes

    def accept(self, payload: bytes | str | dict[str, Any], *, source_id: str, topic: str, qos: int = 0) -> IngressMessage:
        if qos not in {0, 1, 2}:
            raise IngressRejected("MQTT QoS must be 0, 1, or 2")
        return normalize_ingress(payload, transport=IngressTransport.MQTT, source_id=source_id, topic=topic, max_bytes=self.max_bytes)
