from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Any
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel_edge.domain.models import (
    AuthorizedReviewCommand,
    HazardKind,
    PrincipalRef,
    ReviewActionKind,
)
from sentinel_edge.security import AuthorizationError, CommandAuthorizer, canonical_json_bytes, sha256_bytes


class OfflineReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    action: ReviewActionKind
    idempotency_key: str
    until: datetime | None = None

    @model_validator(mode="after")
    def validate_action(self) -> "OfflineReviewRequest":
        if self.action not in {ReviewActionKind.ACKNOWLEDGE, ReviewActionKind.SNOOZE}:
            raise ValueError("offline client supports acknowledge and snooze only")
        if self.action is ReviewActionKind.SNOOZE and self.until is None:
            raise ValueError("offline snooze requires until")
        if not self.idempotency_key.strip():
            raise ValueError("idempotency_key must not be blank")
        return self


class OfflineReviewTicket(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ticket_id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    hazard: HazardKind
    action: ReviewActionKind
    idempotency_key: str
    snooze_until: datetime | None = None
    base_incident_version: int = Field(ge=1)
    issued_at: datetime
    expires_at: datetime
    principal: PrincipalRef
    payload_sha256: str
    authorization_tag: str


class OfflineCommandService:
    """Creates minimal offline tickets and reauthorizes them against current truth."""

    def __init__(self, authorizer: CommandAuthorizer, *, ttl_seconds: int = 900, ticket_secret: bytes | None = None) -> None:
        self.authorizer = authorizer
        self.ttl_seconds = ttl_seconds
        self._ticket_secret = ticket_secret or hashlib.sha256(b"sentinel-edge-development-offline-ticket-v1").digest()
        if len(self._ticket_secret) < 32:
            raise ValueError("offline ticket secret must contain at least 32 bytes")

    def _ticket_body(self, fields: dict) -> dict:
        return {
            "incident_id": str(fields["incident_id"]),
            "hazard": fields["hazard"].value if hasattr(fields["hazard"], "value") else fields["hazard"],
            "action": fields["action"].value if hasattr(fields["action"], "value") else fields["action"],
            "idempotency_key": fields["idempotency_key"],
            "snooze_until": fields.get("snooze_until").isoformat() if fields.get("snooze_until") else None,
            "base_incident_version": fields["base_incident_version"],
            "issued_at": fields["issued_at"].isoformat(),
            "expires_at": fields["expires_at"].isoformat(),
            "principal": fields["principal"].model_dump(mode="json") if hasattr(fields["principal"], "model_dump") else fields["principal"],
        }

    def _sign_ticket(self, body: dict) -> tuple[str, str]:
        digest = sha256_bytes(canonical_json_bytes(body))
        tag = hmac.new(self._ticket_secret, canonical_json_bytes({"payload_sha256": digest}), hashlib.sha256).hexdigest()
        return digest, tag

    @staticmethod
    def payload(ticket_or_fields: dict) -> dict:
        return {
            "incident_id": str(ticket_or_fields["incident_id"]),
            "hazard": ticket_or_fields["hazard"].value if hasattr(ticket_or_fields["hazard"], "value") else ticket_or_fields["hazard"],
            "action": ticket_or_fields["action"].value if hasattr(ticket_or_fields["action"], "value") else ticket_or_fields["action"],
            "snooze_until": ticket_or_fields.get("snooze_until").isoformat() if ticket_or_fields.get("snooze_until") else None,
            "idempotency_key": ticket_or_fields["idempotency_key"],
            "base_incident_version": ticket_or_fields["base_incident_version"],
        }

    def prepare(self, incident: Any, request: OfflineReviewRequest, principal: PrincipalRef, *, now: datetime | None = None) -> OfflineReviewTicket:
        now = now or datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self.ttl_seconds)
        fields = {
            "incident_id": incident.incident_id,
            "hazard": incident.hazard,
            "action": request.action,
            "snooze_until": request.until,
            "idempotency_key": request.idempotency_key,
            "base_incident_version": incident.version,
            "issued_at": now,
            "expires_at": expires_at,
            "principal": principal,
        }
        digest, tag = self._sign_ticket(self._ticket_body(fields))
        return OfflineReviewTicket(
            incident_id=incident.incident_id,
            hazard=incident.hazard,
            action=request.action,
            idempotency_key=request.idempotency_key,
            snooze_until=request.until,
            base_incident_version=incident.version,
            issued_at=now,
            expires_at=expires_at,
            principal=principal,
            payload_sha256=digest,
            authorization_tag=tag,
        )

    def reconcile(self, ticket: OfflineReviewTicket, current_incident: Any, principal: PrincipalRef, *, now: datetime | None = None) -> Any:
        now = now or datetime.now(timezone.utc)
        body = self._ticket_body(ticket.model_dump())
        digest, expected_tag = self._sign_ticket(body)
        if not secrets.compare_digest(digest, ticket.payload_sha256) or not secrets.compare_digest(expected_tag, ticket.authorization_tag):
            raise AuthorizationError("offline command ticket authentication failed")
        if ticket.expires_at <= now:
            raise AuthorizationError("offline command expired; reconfirmation required")
        if ticket.principal != principal:
            raise AuthorizationError("offline command principal or trust epoch changed")
        if ticket.incident_id != current_incident.incident_id or ticket.hazard != current_incident.hazard:
            raise AuthorizationError("offline command incident identity changed")
        if ticket.base_incident_version != current_incident.version:
            raise AuthorizationError("offline command base incident version is stale")
        payload = self.payload(ticket.model_dump())
        operation = f"incidents:{ticket.action.value}"
        target = f"incident:{ticket.incident_id}"
        fresh = self.authorizer.decide(principal, operation=operation, target=target, payload={
            "incident_id": str(ticket.incident_id),
            "hazard": ticket.hazard.value,
            "action": ticket.action.value,
            "snooze_until": ticket.snooze_until.isoformat() if ticket.snooze_until else None,
            "comment": None,
            "idempotency_key": ticket.idempotency_key,
        }, accepted_at=now)
        return AuthorizedReviewCommand(
            incident_id=ticket.incident_id,
            hazard=ticket.hazard,
            action=ticket.action,
            snooze_until=ticket.snooze_until,
            idempotency_key=ticket.idempotency_key,
            authorization=fresh,
            payload_sha256=fresh.payload_sha256,
            submitted_at=now,
        )
