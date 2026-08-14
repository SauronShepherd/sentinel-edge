"""Component-4 collaboration service and explainable correlation decisions."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol

from .metrics import CollaborationMetrics
from .models import CollaborativeSignalEnvelope, CorrelationDecisionRecord
from .policy import CollaborationPolicy, evaluate_correlation, load_policy
from .repository import CollaborationRepository


class CollaborativeIncidentWriter(Protocol):
    """Narrow Component-4-owned integration port.

    Implementations may create/update an incident using normal Component-4
    state logic.  Transports, API handlers and clients must never implement
    this authority.
    """
    def apply_collaboration_decision(self, decision: CorrelationDecisionRecord) -> str | None: ...


@dataclass
class CollaborativeCorrelationService:
    repository: CollaborationRepository = field(default_factory=CollaborationRepository)
    policy: CollaborationPolicy = field(default_factory=load_policy)
    metrics: CollaborationMetrics = field(default_factory=CollaborationMetrics)
    incident_writer: CollaborativeIncidentWriter | None = None

    def ingest(self, envelope: CollaborativeSignalEnvelope, *, now: datetime | None = None) -> CorrelationDecisionRecord:
        now = now or datetime.now(timezone.utc)
        if envelope.validation_state == "rejected":
            raise ValueError("REJECTED_ENVELOPE_CANNOT_ENTER_CORRELATOR")
        if not self.repository.add_envelope(envelope):
            self.metrics.inc("collaboration_duplicates_total", kind="signal")
            raise ValueError("SIGNAL_DUPLICATE")
        self.metrics.inc(
            "collaboration_inbound_total",
            validation_state=envelope.validation_state,
            transport_trust=envelope.transport_trust,
        )

        episode = self.repository.episode_envelopes(envelope)
        signals = [item.signal for item in episode if item.validation_state == "admitted"]
        if not signals:
            # Context-only input produces an explicit non-strengthening record.
            signals = [envelope.signal]
        trust = envelope.transport_trust
        # Mixed transport episodes inherit the weakest admitted trust.  Email
        # cannot be upgraded by being colocated with fixture evidence.
        if any(item.transport_trust == "email_unverified" for item in episode):
            trust = "email_unverified"
        decision = evaluate_correlation(signals, now=now, transport_trust=trust, policy=self.policy)
        if envelope.validation_state == "context_only":
            decision = decision.model_copy(update={
                "selected_action": "context_only",
                "positive_reasons": [],
                "blocking_reasons": list(dict.fromkeys([*decision.blocking_reasons, *envelope.validation_reason_codes, "CONTEXT_ONLY_INPUT"])),
                "created_or_updated_incident_id": None,
            })

        if self.incident_writer is not None and decision.selected_action in {"create_review_incident", "update_incident", "multi_node_trigger_simulated"}:
            incident_id = self.incident_writer.apply_collaboration_decision(decision)
            if incident_id:
                decision = decision.model_copy(update={"created_or_updated_incident_id": incident_id})
        self.repository.add_decision(decision)
        self.metrics.inc("collaboration_correlation_decisions_total", hazard=decision.hazard, action=decision.selected_action)
        active = sum(1 for item in self.repository.decisions() if item.hazard == decision.hazard and item.selected_action != "no_action")
        self.metrics.set_gauge(f"collaboration_correlation_episodes_active.{decision.hazard}", active)
        return decision
