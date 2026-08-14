from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from sentinel_edge.domain.models import (
    AnalysisResult,
    AuthorizedReviewCommand,
    CommandReceipt,
    CommandStatus,
    CoverageState,
    HazardKind,
    IncidentRecord,
    IncidentReviewState,
    IncidentState,
    IncidentStatusCommand,
    IncidentCommandKind,
    IncidentLabel,
    IncidentRelation,
    IncidentRelationKind,
    NotificationIntent,
    NotificationStatus,
    ReviewAction,
)
from sentinel_edge.incidents.human_factors import NotificationDispatcher, NotificationSender
from sentinel_edge.authority import AuthorityWatermark
from sentinel_edge.storage import IncidentJournalStore
from sentinel_edge.security import CommandAuthorizer, AuthorizationError, sha256_bytes, canonical_json_bytes


_ALLOWED = {
    IncidentState.NORMAL: {IncidentState.NORMAL, IncidentState.WATCH, IncidentState.SUSPECTED, IncidentState.CONFIRMED, IncidentState.DEGRADED},
    IncidentState.WATCH: {IncidentState.NORMAL, IncidentState.WATCH, IncidentState.SUSPECTED, IncidentState.CONFIRMED, IncidentState.DEGRADED},
    IncidentState.SUSPECTED: {IncidentState.WATCH, IncidentState.SUSPECTED, IncidentState.CONFIRMED, IncidentState.RESOLVING, IncidentState.DEGRADED},
    IncidentState.CONFIRMED: {IncidentState.CONFIRMED, IncidentState.RESOLVING, IncidentState.DEGRADED},
    IncidentState.RESOLVING: {IncidentState.CONFIRMED, IncidentState.RESOLVING, IncidentState.RESOLVED, IncidentState.DEGRADED},
    IncidentState.RESOLVED: {IncidentState.RESOLVED, IncidentState.WATCH, IncidentState.SUSPECTED, IncidentState.CONFIRMED, IncidentState.DEGRADED},
    IncidentState.DEGRADED: {IncidentState.DEGRADED, IncidentState.WATCH, IncidentState.SUSPECTED, IncidentState.CONFIRMED},
}

_NOTIFY_STATES = {
    IncidentState.WATCH,
    IncidentState.SUSPECTED,
    IncidentState.CONFIRMED,
    IncidentState.DEGRADED,
}


class IncidentEventEngine:
    """Component 4: sole lifecycle, review, authority-journal, and notification-intent writer."""

    component_id = "component-4-incidents"

    def __init__(
        self,
        store: IncidentJournalStore | None = None,
        *,
        notification_budget: int = 8,
        command_authorizer: CommandAuthorizer | None = None,
    ) -> None:
        self._store = store or IncidentJournalStore()
        self.command_authorizer = command_authorizer or CommandAuthorizer.development()
        self._current: dict[HazardKind, IncidentRecord] = {
            item.hazard: item for item in self._store.latest_by_hazard()
        }
        self.notification_budget = notification_budget

    def apply_analysis(self, analysis: AnalysisResult, accepted_at: datetime | None = None) -> IncidentRecord:
        accepted_at = accepted_at or datetime.now(timezone.utc)
        current = self._current.get(analysis.hazard)
        if current and analysis.analysis_id in current.analysis_ids:
            return current
        event_time = analysis.event_time or analysis.produced_at
        if current and current.event_time_watermark is not None and event_time < current.event_time_watermark:
            # Late corrections remain durable history, but can never create a
            # fresh alert or move the authoritative event-time watermark.
            state_rank = {
                IncidentState.NORMAL: 0,
                IncidentState.WATCH: 1,
                IncidentState.SUSPECTED: 2,
                IncidentState.CONFIRMED: 3,
                IncidentState.DEGRADED: 1,
                IncidentState.RESOLVING: 1,
            }
            if analysis.score <= current.confidence and state_rank.get(analysis.state_hint, 0) <= state_rank.get(current.state, 0):
                return current
            correction = current.model_copy(update={
                "last_observed_at": accepted_at,
                "version": current.version + 1,
                "reason_codes": tuple(sorted(set(current.reason_codes + tuple(analysis.reason_codes) + ("late_context_correction",)))),
                "analysis_ids": current.analysis_ids + (analysis.analysis_id,),
                "correlation_ids": current.correlation_ids + (analysis.correlation_id,),
            })
            self._store.append_incident_with_notification(correction, None)
            self._current[analysis.hazard] = correction
            return correction
        target = analysis.state_hint
        reasons = list(analysis.reason_codes)
        if analysis.abstained or analysis.coverage is CoverageState.BLIND:
            target = IncidentState.DEGRADED
            reasons.append("coverage_prevents_strong_state")
        if current and target is IncidentState.NORMAL and current.state in {IncidentState.SUSPECTED, IncidentState.CONFIRMED}:
            target = IncidentState.RESOLVING
            reasons.append("negative_evidence_requires_resolution_window")
        previous_state = current.state if current else IncidentState.NORMAL
        if target not in _ALLOWED[previous_state]:
            raise ValueError(f"illegal incident transition {previous_state}->{target}")
        label = IncidentLabel.UNCERTAIN if analysis.abstained else (
            IncidentLabel.CONFIRM if target is IncidentState.CONFIRMED else IncidentLabel.REJECT
        )
        record = IncidentRecord(
            incident_id=current.incident_id if current else (analysis.incident_id_hint or uuid5(
                NAMESPACE_URL, f"sentinel-incident:{analysis.hazard.value}:{analysis.correlation_id}"
            )),
            hazard=analysis.hazard,
            state=target,
            confidence=analysis.score,
            coverage=analysis.coverage,
            source_mode=analysis.source_mode,
            first_observed_at=current.first_observed_at if current else event_time,
            last_observed_at=accepted_at,
            event_time_watermark=max(event_time, current.event_time_watermark) if current and current.event_time_watermark else event_time,
            version=(current.version + 1) if current else 1,
            reason_codes=tuple(sorted(set((current.reason_codes if current else ()) + tuple(reasons)))),
            analysis_ids=(current.analysis_ids if current else ()) + (analysis.analysis_id,),
            correlation_ids=(current.correlation_ids if current else ()) + (analysis.correlation_id,),
            last_boot_id=analysis.boot_id,
            source_lineage=analysis.source_lineage,
            model_profile_id=analysis.model_profile_id,
            config_hashes=analysis.config_hashes,
            labels=(current.labels if current else ()) + (label,),
        )
        notification = self._notification_for(record, previous_state, accepted_at)
        self._store.append_incident_with_notification(record, notification)
        self._current[analysis.hazard] = record
        return record

    def _notification_for(
        self, record: IncidentRecord, previous_state: IncidentState, accepted_at: datetime
    ) -> NotificationIntent | None:
        if record.state not in _NOTIFY_STATES or record.state is previous_state:
            return None
        review = self._store.review_state(str(record.incident_id))
        status = NotificationStatus.PENDING
        reasons = ["incident_state_changed"]
        if review.snoozed_until and review.snoozed_until > accepted_at:
            if record.state is IncidentState.CONFIRMED:
                reasons.append("snooze_overridden_by_confirmation")
            else:
                status = NotificationStatus.SUPPRESSED
                reasons.append("incident_snoozed")
        count = self._store.notification_count(str(record.incident_id))
        if count >= self.notification_budget and record.state is not IncidentState.CONFIRMED:
            status = NotificationStatus.SUPPRESSED
            reasons.append("notification_budget_exhausted")
        idempotency_key = f"incident:{record.incident_id}:version:{record.version}:state:{record.state.value}"
        return NotificationIntent(
            notification_id=uuid5(NAMESPACE_URL, f"sentinel-notification:{idempotency_key}"),
            incident_id=record.incident_id,
            hazard=record.hazard,
            incident_version=record.version,
            incident_state=record.state,
            idempotency_key=idempotency_key,
            status=status,
            created_at=accepted_at,
            updated_at=accepted_at,
            reason_codes=tuple(reasons),
        )

    def incident_by_id(self, incident_id: str) -> IncidentRecord | None:
        current = next((item for item in self._current.values() if item.incident_id == incident_id), None)
        if current is not None:
            return current
        history = [item for item in self._store.all() if item.incident_id == incident_id]
        return max(history, key=lambda item: item.version) if history else None

    def apply_status_command(self, command: IncidentStatusCommand) -> IncidentRecord | IncidentRelation:
        current = self.incident_by_id(command.incident_id)
        if current is None or current.hazard is not command.hazard:
            raise ValueError("incident command target not found")
        target_key = f"incident-status:{command.incident_id}:{command.command.value}"
        scoped = sha256_bytes(canonical_json_bytes({
            "actor": command.actor,
            "target": target_key,
            "idempotency_key": command.idempotency_key,
        }))
        existing = self._store.command_receipt(scoped)
        payload = {
            "incident_id": str(command.incident_id),
            "hazard": command.hazard.value,
            "command": command.command.value,
            "expected_version": command.expected_version,
            "actor": command.actor,
            "reason": command.reason,
            "related_incident_id": str(command.related_incident_id) if command.related_incident_id else None,
            "related_hazard": command.related_hazard.value if command.related_hazard else None,
            "idempotency_key": command.idempotency_key,
        }
        payload_sha = sha256_bytes(canonical_json_bytes(payload))
        if existing is not None:
            if existing.payload_sha256 != payload_sha:
                raise ValueError("idempotency key conflict")
            if command.command in {IncidentCommandKind.LINK, IncidentCommandKind.MERGE}:
                relation = next((item for item in self._store.incident_relations() if str(item.relation_id) == existing.result_sha256), None)
                if relation is not None:
                    return relation
            refreshed = self.incident_by_id(command.incident_id)
            assert refreshed is not None
            return refreshed

        if current.version != command.expected_version:
            raise ValueError("stale incident command requires reconfirmation")

        if command.command in {IncidentCommandKind.LINK, IncidentCommandKind.MERGE}:
            assert command.related_incident_id is not None and command.related_hazard is not None
            related = self.incident_by_id(command.related_incident_id)
            if related is None or related.hazard is not command.related_hazard:
                raise ValueError("related incident not found")
            if command.command is IncidentCommandKind.MERGE:
                if related.hazard is not current.hazard:
                    raise ValueError("merge requires the same hazard; use link for cross-hazard context")
                relation_kind = IncidentRelationKind.MERGED_ALIAS
            else:
                if related.hazard is current.hazard:
                    raise ValueError("same-hazard incidents require merge rather than cross-hazard link")
                relation_kind = IncidentRelationKind.TEMPORAL_ASSOCIATION
            relation = IncidentRelation(
                relation_id=uuid5(NAMESPACE_URL, f"sentinel-incident-relation:{command.command_id}"),
                source_incident_id=current.incident_id,
                source_hazard=current.hazard,
                target_incident_id=related.incident_id,
                target_hazard=related.hazard,
                relation=relation_kind,
                confidence=1.0,
                expected_source_version=current.version,
                expected_target_version=related.version,
                created_at=command.submitted_at,
                actor=command.actor,
                reason=command.reason,
            )
            relation = self._store.record_incident_relation(relation)
            receipt = CommandReceipt(
                command_id=command.command_id,
                principal_id=command.actor,
                operation=f"incidents:{command.command.value}",
                target=target_key,
                scoped_idempotency_key=scoped,
                payload_sha256=payload_sha,
                status=CommandStatus.COMMITTED,
                accepted_at=command.submitted_at,
                committed_at=command.submitted_at,
                result_version=current.version,
                result_sha256=str(relation.relation_id),
                reason_codes=("expected_version_verified", "incident_relation_committed"),
            )
            self._store.record_command_receipt(receipt)
            return relation

        target_state = current.state
        confidence = current.confidence
        reasons = list(current.reason_codes) + [f"operator_{command.command.value}", f"reason:{command.reason}"]
        if command.command is IncidentCommandKind.CORROBORATE:
            confidence = min(1.0, current.confidence + 0.05)
        elif command.command is IncidentCommandKind.CONTRADICT:
            confidence = max(0.0, current.confidence - 0.10)
        elif command.command is IncidentCommandKind.RESOLVE:
            if current.coverage is CoverageState.BLIND:
                raise ValueError("blind required sensor cannot resolve an event")
            review_state = self.review_state(str(current.incident_id))
            if current.state is IncidentState.CONFIRMED and review_state.acknowledged_at is None:
                raise ValueError("unreviewed high-severity incident cannot be auto-closed")
            target_state = IncidentState.RESOLVED if current.state is IncidentState.RESOLVING else IncidentState.RESOLVING
        elif command.command is IncidentCommandKind.REOPEN:
            if current.state is not IncidentState.RESOLVED:
                raise ValueError("only a resolved incident can be reopened")
            target_state = IncidentState.SUSPECTED
        elif command.command is IncidentCommandKind.CONTROL:
            reasons.append("controlled_activity_recorded")
        if target_state not in _ALLOWED[current.state]:
            raise ValueError(f"illegal incident command transition {current.state}->{target_state}")
        labels = current.labels
        if command.command is IncidentCommandKind.CONTROL and IncidentLabel.CONTROL not in labels:
            labels = labels + (IncidentLabel.CONTROL,)
        record = current.model_copy(update={
            "state": target_state,
            "confidence": confidence,
            "last_observed_at": command.submitted_at,
            "version": current.version + 1,
            "reason_codes": tuple(sorted(set(reasons))),
            "labels": labels,
        })
        notification = self._notification_for(record, current.state, command.submitted_at)
        self._store.append_incident_with_notification(record, notification)
        self._current[current.hazard] = record
        receipt = CommandReceipt(
            command_id=command.command_id,
            principal_id=command.actor,
            operation=f"incidents:{command.command.value}",
            target=target_key,
            scoped_idempotency_key=scoped,
            payload_sha256=payload_sha,
            status=CommandStatus.COMMITTED,
            accepted_at=command.submitted_at,
            committed_at=command.submitted_at,
            result_version=record.version,
            result_sha256=sha256_bytes(canonical_json_bytes(record.model_dump(mode="json"))),
            reason_codes=("expected_version_verified", "component4_incident_command_committed"),
        )
        self._store.record_command_receipt(receipt)
        return record

    def incident_relations(self) -> tuple[IncidentRelation, ...]:
        return self._store.incident_relations()

    def review(self, action: ReviewAction) -> IncidentReviewState:
        current = self._current.get(action.hazard)
        if current is None or current.incident_id != action.incident_id:
            raise ValueError("review action does not target the current incident")
        return self._store.record_review(action)

    @staticmethod
    def _authorized_review_payload(command: AuthorizedReviewCommand) -> dict:
        return {
            "incident_id": str(command.incident_id),
            "hazard": command.hazard.value,
            "action": command.action.value,
            "snooze_until": command.snooze_until.isoformat() if command.snooze_until else None,
            "comment": command.comment,
            "idempotency_key": command.idempotency_key,
        }

    def apply_authorized_review(self, command: AuthorizedReviewCommand) -> tuple[IncidentReviewState, CommandReceipt]:
        payload = self._authorized_review_payload(command)
        target = f"incident:{command.incident_id}"
        operation = f"incidents:{command.action.value}"
        self.command_authorizer.verify(
            command.authorization,
            payload=payload,
            operation=operation,
            target=target,
            current_principal=command.authorization.principal,
            now=command.submitted_at,
        )
        scoped_key = self.command_authorizer.scoped_idempotency_key(
            command.authorization.principal,
            operation=operation,
            target=target,
            client_key=command.idempotency_key,
        )
        existing = self._store.command_receipt(scoped_key)
        if existing is not None:
            if existing.payload_sha256 != command.payload_sha256:
                raise ValueError("idempotency key conflict")
            return self.review_state(str(command.incident_id)), existing
        state = self.review(
            ReviewAction(
                review_id=command.command_id,
                incident_id=command.incident_id,
                hazard=command.hazard,
                action=command.action,
                actor=command.authorization.principal.principal_id,
                created_at=command.submitted_at,
                snooze_until=command.snooze_until,
                comment=command.comment,
            )
        )
        result_payload = state.model_dump(mode="json")
        receipt = CommandReceipt(
            command_id=command.command_id,
            principal_id=command.authorization.principal.principal_id,
            operation=operation,
            target=target,
            scoped_idempotency_key=scoped_key,
            payload_sha256=command.payload_sha256,
            status=CommandStatus.COMMITTED,
            accepted_at=command.authorization.accepted_at,
            committed_at=command.submitted_at,
            result_version=state.review_count,
            result_sha256=sha256_bytes(canonical_json_bytes(result_payload)),
            reason_codes=("gateway_authorization_verified", "component4_committed"),
        )
        return state, self._store.record_command_receipt(receipt)

    def command_receipts(self) -> tuple[CommandReceipt, ...]:
        return self._store.command_receipts()

    def storage_diagnostics(self) -> dict[str, object]:
        return {
            "durability": self._store.durability_profile(),
            "integrity_check": self._store.integrity_check(),
            "authority_conformance": self._store.authority_conformance(),
        }

    def checkpoint_storage(self, mode: str = "PASSIVE") -> dict[str, int | float | str]:
        return self._store.checkpoint(mode)

    def dispatch_notifications(self, sender: NotificationSender) -> tuple[NotificationIntent, ...]:
        return NotificationDispatcher(self._store, sender).dispatch()

    def current(self) -> tuple[IncidentRecord, ...]:
        return tuple(sorted(self._current.values(), key=lambda item: item.hazard.value))

    def journal(self) -> tuple[IncidentRecord, ...]:
        return self._store.all()

    def authority_journal(self) -> tuple[Any, ...]:
        return self._store.authority_journal()

    def authority_conformance(self) -> dict[str, object]:
        return self._store.authority_conformance()

    def authority_watermark(self) -> AuthorityWatermark:
        return AuthorityWatermark.from_conformance(self._store.authority_conformance())

    def projection_conformance(self) -> dict[str, object]:
        failures: list[str] = []
        durable = {item.hazard: item for item in self._store.latest_by_hazard()}
        if set(durable) != set(self._current):
            failures.append("projection_hazard_set_mismatch")
        for hazard in sorted(set(durable) | set(self._current), key=lambda item: item.value):
            left = durable.get(hazard)
            right = self._current.get(hazard)
            if left is None or right is None:
                continue
            if left.incident_id != right.incident_id or left.version != right.version or left.state != right.state:
                failures.append(f"projection_divergence:{hazard.value}")
        authority = self._store.authority_conformance()
        if not authority["valid"]:
            failures.append("authority_journal_invalid")
        return {
            "valid": not failures,
            "authority_watermark": authority["highest_contiguous_position"],
            "failures": tuple(failures),
        }

    def notifications(self) -> tuple[NotificationIntent, ...]:
        return self._store.notifications()

    def notification_metrics(self, now: datetime | None = None) -> dict[str, int | float]:
        return self._store.notification_metrics(now)

    def reviews(self) -> tuple[ReviewAction, ...]:
        return self._store.reviews()

    def review_state(self, incident_id: str) -> IncidentReviewState:
        return self._store.review_state(incident_id)

    def review_metrics(self, now: datetime | None = None) -> dict[str, int]:
        now = now or datetime.now(timezone.utc)
        states = self._store.review_states()
        return {
            "acknowledged": sum(item.acknowledged_at is not None for item in states),
            "active_snoozes": sum(item.snoozed_until is not None and item.snoozed_until > now for item in states),
            "expired_snoozes": sum(item.snoozed_until is not None and item.snoozed_until <= now for item in states),
            "review_actions": len(self.reviews()),
        }

    def workflow_metrics(self) -> dict[str, object]:
        """Return elapsed acknowledgement/review timings from local audit records."""
        values: list[float] = []
        for incident in self.current():
            review = self.review_state(str(incident.incident_id))
            if review.acknowledged_at is None:
                continue
            notifications = [item for item in self.notifications() if item.incident_id == incident.incident_id]
            if notifications:
                values.append(max(0.0, (review.acknowledged_at - min(item.created_at for item in notifications)).total_seconds()))
        return {
            "schema": "sentinel-edge-operator-workflow-metrics/1.0",
            "acknowledgement_time_seconds": sorted(values),
            "review_action_count": len(self.reviews()),
            "acknowledged_count": len(values),
        }

    def notification_streams(self) -> tuple[dict, ...]:
        notifications = self.notifications()
        streams: list[dict] = []
        for incident in self.current():
            related = [item for item in notifications if item.incident_id == incident.incident_id]
            review = self.review_state(str(incident.incident_id))
            streams.append({
                "incident_id": str(incident.incident_id),
                "hazard": incident.hazard.value,
                "state": incident.state.value,
                "evidence_update_count": len(incident.analysis_ids),
                "notification_count": len(related),
                "notification_statuses": [item.status.value for item in related],
                "acknowledged_at": review.acknowledged_at.isoformat() if review.acknowledged_at else None,
                "snoozed_until": review.snoozed_until.isoformat() if review.snoozed_until else None,
            })
        return tuple(streams)
