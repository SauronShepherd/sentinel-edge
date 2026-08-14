from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Iterable
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel_edge.collector import BoundedBackgroundConnector
from sentinel_edge.security import (
    GrantLifecycleAction,
    KeyLifecycleAction,
    KeyPurpose,
    KeyState,
    canonical_json_bytes,
    sha256_bytes,
)




class NetworkExposureEvidence(BaseModel):
    """Observed application-level network-removal evidence, not a host forensics claim."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True)

    schema_id: str = Field(default="sentinel-edge-network-exposure-evidence/1.0", alias="schema")
    observed_at: datetime
    observer: str
    listening_endpoints: tuple[str, ...] = ()
    permitted_loopback_endpoints: tuple[str, ...] = ()
    firewall_default_deny: bool
    ingress_rules_removed: bool
    service_bindings_removed: bool
    external_probe_results: dict[str, str]
    evidence_sha256: str

    @model_validator(mode="before")
    @classmethod
    def verify_digest(cls, value: str) -> str:
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        observed = payload.pop("evidence_sha256", None)
        expected = sha256_bytes(canonical_json_bytes(payload))
        if observed != expected:
            raise ValueError("network exposure evidence digest mismatch")
        return value

    @property
    def exposure_removed(self) -> bool:
        forbidden = set(self.listening_endpoints) - set(self.permitted_loopback_endpoints)
        probes_blocked = bool(self.external_probe_results) and all(
            result in {"blocked", "refused", "unreachable"} for result in self.external_probe_results.values()
        )
        return (
            not forbidden
            and self.firewall_default_deny
            and self.ingress_rules_removed
            and self.service_bindings_removed
            and probes_blocked
        )

    @classmethod
    def create(
        cls,
        *,
        observed_at: datetime,
        observer: str,
        listening_endpoints: tuple[str, ...] = (),
        permitted_loopback_endpoints: tuple[str, ...] = (),
        firewall_default_deny: bool,
        ingress_rules_removed: bool,
        service_bindings_removed: bool,
        external_probe_results: dict[str, str],
    ) -> "NetworkExposureEvidence":
        base = {
            "schema": "sentinel-edge-network-exposure-evidence/1.0",
            "observed_at": observed_at.isoformat(),
            "observer": observer,
            "listening_endpoints": list(listening_endpoints),
            "permitted_loopback_endpoints": list(permitted_loopback_endpoints),
            "firewall_default_deny": firewall_default_deny,
            "ingress_rules_removed": ingress_rules_removed,
            "service_bindings_removed": service_bindings_removed,
            "external_probe_results": external_probe_results,
        }
        return cls(**base, evidence_sha256=sha256_bytes(canonical_json_bytes(base)))


class DecommissionState(StrEnum):
    COMPLETED = "completed"
    BLOCKED = "blocked"


class DecommissionReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    receipt_id: UUID
    state: DecommissionState
    actor: str
    reason: str
    created_at: datetime
    connector_receipts: tuple[dict[str, Any], ...]
    protected_state_purge_receipts: tuple[dict[str, Any], ...]
    key_lifecycle_events: tuple[dict[str, Any], ...]
    network_exposure_removed: bool
    network_exposure_proven: bool
    network_exposure_evidence: dict[str, Any] | None = None
    authority_watermark: dict[str, Any]
    unresolved_disposition_request_ids: tuple[str, ...]
    pending_notification_ids: tuple[str, ...]
    pending_critical_spool_items: int = Field(ge=0)
    blockers: tuple[str, ...]
    historical_identity_preserved: bool
    secure_erasure_claimed: bool = False
    receipt_sha256: str


class DecommissionManager:
    """Fail-closed operational retirement coordinator.

    This proves application-level quiescence and authority revocation. It does not
    claim flash secure erasure, firmware reset, physical media destruction, or
    removal from external systems that did not return a receipt.
    """

    def __init__(self, engine: Any) -> None:
        self.engine = engine

    def execute(
        self,
        *,
        actor: str,
        reason: str,
        connectors: Iterable[BoundedBackgroundConnector] = (),
        connector_deadline_seconds: float = 1.0,
        network_exposure_removed: bool | None = None,
        network_exposure_evidence: NetworkExposureEvidence | None = None,
        now: datetime | None = None,
    ) -> DecommissionReceipt:
        if not actor.strip() or not reason.strip():
            raise ValueError("decommission actor and reason are required")
        now = now or datetime.now(timezone.utc)
        connector_receipts = tuple(
            {
                "connector_id": receipt.connector_id,
                "state": receipt.state.value,
                "accepted_items": receipt.accepted_items,
                "processed_items": receipt.processed_items,
                "cancelled_items": receipt.cancelled_items,
                "thread_alive": receipt.thread_alive,
                "stopped_at": receipt.stopped_at.isoformat(),
                "deadline_seconds": receipt.deadline_seconds,
                "reason_codes": list(receipt.reason_codes),
            }
            for receipt in (connector.drain_and_stop(deadline_seconds=connector_deadline_seconds) for connector in connectors)
        )
        blockers: list[str] = []
        if any(item["thread_alive"] or item["state"] != "stopped" for item in connector_receipts):
            blockers.append("connector_shutdown_incomplete")

        unresolved = tuple(
            str(item.request_id)
            for item in self.engine.disposition.requests()
            if item.status.value in {"restricted", "in_progress", "external_recipient_pending", "failed"}
        )
        if unresolved:
            blockers.append("unresolved_disposition_requests")

        pending_notifications = tuple(
            str(item.notification_id)
            for item in self.engine.incidents.notifications()
            if item.status.value in {"pending", "failed", "delivering"}
        )
        if pending_notifications:
            blockers.append("pending_notification_effects")

        spool_metrics = self.engine.critical_spool.metrics()
        pending_spool = int(spool_metrics.pending_items)
        if pending_spool:
            blockers.append("pending_critical_spool_items")

        purge_receipts: list[dict[str, Any]] = []
        for grant in self.engine.protected_state.grants():
            if grant.state.value == "active":
                receipt = self.engine.protected_state.revoke(
                    grant.grant_id,
                    action=GrantLifecycleAction.PLANNED_RETIREMENT,
                    actor=actor,
                    reason=f"decommission:{reason}",
                    now=now,
                )
                purge_receipts.append(receipt.model_dump(mode="json"))

        key_events: list[dict[str, Any]] = []
        for record in self.engine.key_lifecycle.records():
            if record.state is not KeyState.ACTIVE:
                continue
            action = (
                KeyLifecycleAction.RETIRE
                if record.purpose is KeyPurpose.AUDIT_SIGNING
                else KeyLifecycleAction.REVOKE_POLICY
            )
            event = self.engine.key_lifecycle.transition(
                identity_id=record.identity_id,
                generation=record.generation,
                purpose=record.purpose,
                action=action,
                actor=actor,
                reason=f"decommission:{reason}",
                policy_version=record.policy_version,
                effective_at=now,
            )
            key_events.append(event.model_dump(mode="json"))

        evidence_removed = network_exposure_evidence.exposure_removed if network_exposure_evidence else None
        if network_exposure_removed is None:
            network_exposure_removed = bool(evidence_removed)
        if evidence_removed is False:
            blockers.append("network_exposure_evidence_failed")
        if not network_exposure_removed:
            blockers.append("network_exposure_not_removed")
        authority_watermark = self.engine.incidents.authority_watermark().model_dump(mode="json")
        state = DecommissionState.COMPLETED if not blockers else DecommissionState.BLOCKED
        base = {
            "state": state.value,
            "actor": actor,
            "reason": reason,
            "created_at": now.isoformat(),
            "connector_receipts": connector_receipts,
            "protected_state_purge_receipts": purge_receipts,
            "key_lifecycle_events": key_events,
            "network_exposure_removed": network_exposure_removed,
            "network_exposure_proven": bool(network_exposure_evidence and evidence_removed),
            "network_exposure_evidence": network_exposure_evidence.model_dump(mode="json") if network_exposure_evidence else None,
            "authority_watermark": authority_watermark,
            "unresolved_disposition_request_ids": unresolved,
            "pending_notification_ids": pending_notifications,
            "pending_critical_spool_items": pending_spool,
            "blockers": sorted(set(blockers)),
            "historical_identity_preserved": True,
            "secure_erasure_claimed": False,
        }
        digest = sha256_bytes(canonical_json_bytes(base))
        return DecommissionReceipt(
            receipt_id=uuid5(NAMESPACE_URL, f"sentinel-decommission:{digest}"),
            receipt_sha256=digest,
            **base,
        )
