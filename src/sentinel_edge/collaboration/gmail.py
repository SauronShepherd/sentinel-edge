"""Polling Gmail transport port for experimental collaborative signals.

The connector owns no credentials and mutates no incident state. A deployment
supplies a Gmail API-shaped client and a Component-1 envelope sink.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Awaitable, Callable
from uuid import NAMESPACE_URL, uuid5

from .models import CollaborativeSignalEnvelope
from .wire import CollaborativeInboundValidator, decode_signal_email


@dataclass(frozen=True)
class PollResult:
    accepted: int
    rejected: int
    duplicate: int
    envelopes: tuple[dict[str, Any], ...]
    reason_codes: tuple[str, ...]
    cursor: str | None = None
    heartbeat_at: datetime | None = None


class GmailReceiptStore:
    """Small durable idempotency store for the experimental Gmail receiver.

    The store intentionally persists only transport/signal identifiers.  Raw
    email bytes and collaborative signal payloads are not retained here.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else None
        self.message_ids: set[str] = set()
        self.signal_ids: set[str] = set()
        if self.path and self.path.is_file():
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
                self.message_ids = {str(value) for value in payload.get("message_ids", [])}
                self.signal_ids = {str(value) for value in payload.get("signal_ids", [])}
            except (OSError, json.JSONDecodeError):
                # Fail closed: a corrupt durable receipt store must not be
                # silently treated as an empty idempotency set.
                raise ValueError("COLLABORATION_RECEIPT_STORE_INVALID")

    def has_message(self, message_id: str) -> bool:
        return message_id in self.message_ids

    def has_signal(self, signal_id: str) -> bool:
        return signal_id in self.signal_ids

    def record(self, *, message_id: str, signal_id: str | None = None) -> None:
        self.message_ids.add(message_id)
        if signal_id:
            self.signal_ids.add(signal_id)
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": "sentinel-edge.collaboration-gmail-receipts.v1",
            "message_ids": sorted(self.message_ids),
            "signal_ids": sorted(self.signal_ids),
        }
        temp = self.path.with_name(self.path.name + ".tmp")
        temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        os.replace(temp, self.path)


class GmailCollaborativeSignalConnector:
    def __init__(self, *, client: Any, emit_envelope: Callable[[dict[str, Any]], Awaitable[None]], enabled: bool = False, validator: CollaborativeInboundValidator | None = None, max_inflight: int = 50, receipt_store: GmailReceiptStore | None = None) -> None:
        self.client = client
        self.emit_envelope = emit_envelope
        self.enabled = enabled
        self.validator = validator or CollaborativeInboundValidator()
        self.receipts = receipt_store or GmailReceiptStore()
        self._running = False
        if max_inflight < 1:
            raise ValueError("max_inflight must be positive")
        self.max_inflight = max_inflight
        self._cursor: str | None = None
        self._last_heartbeat: datetime | None = None

    async def validate_config(self) -> dict[str, Any]:
        if not self.enabled:
            return {"valid": True, "enabled": False, "reason": "disabled"}
        return {"valid": all(hasattr(self.client, name) for name in ("list_messages", "get_message", "modify_labels")), "enabled": True, "scope": "https://www.googleapis.com/auth/gmail.modify"}

    async def start(self) -> None:
        self._running = True

    async def readiness(self) -> dict[str, Any]:
        return {"ready": self._running and (await self.validate_config())["valid"], "running": self._running}

    async def drain(self, deadline: datetime) -> dict[str, Any]:
        self._running = False
        return {"drained": datetime.now(timezone.utc) <= deadline, "running": False}

    async def stop(self) -> None:
        self._running = False

    async def poll_once(self, *, received_at: datetime | None = None) -> PollResult:
        heartbeat_at = datetime.now(timezone.utc)
        self._last_heartbeat = heartbeat_at
        if not self.enabled:
            return PollResult(0, 0, 0, (), ("DISABLED",), self._cursor, heartbeat_at)
        received_at = received_at or datetime.now(timezone.utc)
        messages = await self.client.list_messages('subject:"Sentinel Collaborative Signal v1" newer_than:7d')
        accepted = rejected = duplicate = 0
        envelopes: list[dict[str, Any]] = []
        reasons: list[str] = []
        ordered = sorted(messages, key=lambda item: str(item["id"]))
        pending = ordered[: self.max_inflight]
        if len(ordered) > self.max_inflight:
            reasons.append("MAX_INFLIGHT_BOUNDED")
        for message in pending:
            message_id = str(message["id"])
            if self.receipts.has_message(message_id):
                duplicate += 1
                # Converge Gmail labelling after a crash that happened after
                # local durable acceptance but before remote label mutation.
                await self.client.modify_labels(message_id, add=("sentinel/processed",), remove=("sentinel/rejected",))
                continue
            try:
                signal = decode_signal_email(await self.client.get_message(message_id))
                seen_signal_ids = {item["signal"]["signal_id"] for item in envelopes}
                if self.receipts.has_signal(signal.signal_id):
                    seen_signal_ids.add(signal.signal_id)
                decision = self.validator.validate(signal=signal, received_at=received_at, transport_trust="email_unverified", seen_signal_ids=seen_signal_ids)
                if not decision.accepted:
                    raise ValueError(decision.reason_code or "INTERNAL_ERROR")
                validation_state = "context_only" if decision.reason_code in {"DOMAIN_UNKNOWN", "CLOCK_UNSAFE"} else "admitted"
                envelope = CollaborativeSignalEnvelope(
                    received_at=received_at,
                    transport="email",
                    transport_message_id=message_id,
                    transport_trust="email_unverified",
                    signal=signal,
                    validation_state=validation_state,
                    validation_reason_codes=[decision.reason_code] if decision.reason_code else [],
                    correlation_id=str(uuid5(NAMESPACE_URL, f"sentinel-collaboration:gmail:{message_id}:{signal.signal_id}")),
                ).model_dump(mode="json")
                await self.emit_envelope(envelope)
                # Local durable acceptance precedes Gmail label mutation.
                self.receipts.record(message_id=message_id, signal_id=signal.signal_id)
                await self.client.modify_labels(message_id, add=("sentinel/processed",), remove=("sentinel/rejected",))
                envelopes.append(envelope)
                accepted += 1
            except ValueError as exc:
                rejected += 1
                reasons.append(str(exc))
                self.receipts.record(message_id=message_id)
                await self.client.modify_labels(message_id, add=("sentinel/rejected",), remove=())
            self._cursor = message_id
        return PollResult(accepted, rejected, duplicate, tuple(envelopes), tuple(reasons), self._cursor, heartbeat_at)
