from __future__ import annotations

from typing import Any

from sentinel_edge.domain.models import CoverageState, HealthState, IncidentState, ReviewActionKind
from sentinel_edge.security import canonical_json_bytes, sha256_bytes
from sentinel_edge.storage import ArtifactPolicy, ArtifactRef, ArtifactScope, ContentAddressedArtifactStore


class AfterEventReviewBuilder:
    """Deterministic evidence-derived review; it never invents causes or actions."""

    schema = "sentinel-edge-after-event-review/1.0"

    def build(self, engine: Any, scenario_result: Any) -> dict[str, Any]:
        authority = [item.model_dump(mode="json") for item in engine.incidents.authority_journal()]
        source_events = [item.model_dump(mode="json") for item in engine.collector.health_events()]
        opportunities = [item.model_dump(mode="json") for item in engine.runtime.opportunities.records()]
        incidents = [item.model_dump(mode="json") for item in engine.incidents.current()]
        reviews = [item.model_dump(mode="json") for item in engine.incidents.reviews()]
        notifications = [item.model_dump(mode="json") for item in engine.incidents.notifications()]

        coverage_gaps = [
            {
                "kind": "incident_coverage",
                "hazard": item["hazard"],
                "coverage": item["coverage"],
                "incident_id": item["incident_id"],
            }
            for item in incidents
            if item["coverage"] != CoverageState.SUFFICIENT.value
        ]
        coverage_gaps.extend(
            {
                "kind": "source_health",
                "source_id": item.source_id,
                "state": item.state.value,
                "reason_codes": list(item.reason_codes),
            }
            for item in engine.collector.health()
            if item.state is not HealthState.HEALTHY
        )

        delay_records: list[dict[str, Any]] = []
        for item in engine.runtime.opportunities.records():
            queue_delay_ms = None
            service_ms = None
            deadline_missed = False
            if item.queue_started_monotonic_ns is not None and item.service_started_monotonic_ns is not None:
                queue_delay_ms = (item.service_started_monotonic_ns - item.queue_started_monotonic_ns) / 1_000_000
            if item.service_started_monotonic_ns is not None and item.completed_monotonic_ns is not None:
                service_ms = (item.completed_monotonic_ns - item.service_started_monotonic_ns) / 1_000_000
            if item.completed_monotonic_ns is not None and item.deadline_monotonic_ns is not None:
                deadline_missed = item.completed_monotonic_ns > item.deadline_monotonic_ns
            if queue_delay_ms or deadline_missed or item.reason_codes:
                delay_records.append(
                    {
                        "opportunity_id": str(item.opportunity_id),
                        "workload_id": item.workload_id,
                        "queue_delay_ms": queue_delay_ms,
                        "service_ms": service_ms,
                        "deadline_missed": deadline_missed,
                        "reason_codes": list(item.reason_codes),
                    }
                )

        unresolved: list[dict[str, Any]] = []
        for incident in engine.incidents.current():
            review_state = engine.incidents.review_state(str(incident.incident_id))
            if incident.state in {IncidentState.SUSPECTED, IncidentState.CONFIRMED} and review_state.acknowledged_at is None:
                unresolved.append(
                    {
                        "incident_id": str(incident.incident_id),
                        "hazard": incident.hazard.value,
                        "state": incident.state.value,
                        "action": "acknowledgement_required",
                    }
                )

        operator_comments = [
            {
                "review_id": item["review_id"],
                "incident_id": item["incident_id"],
                "actor": item["actor"],
                "comment": item["comment"],
                "created_at": item["created_at"],
            }
            for item in reviews
            if item["action"] == ReviewActionKind.COMMENT.value
        ]

        review = {
            "schema": self.schema,
            "scenario_id": scenario_result.scenario_id,
            "generation_policy": "deterministic_structured_evidence_only",
            "summary": {
                "observations": scenario_result.observations,
                "analyses": scenario_result.analyses,
                "incident_versions": scenario_result.incident_versions,
                "authority_mutations": scenario_result.authority_mutations,
                "final_states": scenario_result.final_states,
                "source_health": scenario_result.source_health,
                "opportunity_counts": scenario_result.opportunity_counts,
                "notification_metrics": scenario_result.notification_metrics,
            },
            "authority_watermark": engine.incidents.authority_watermark().model_dump(mode="json"),
            "timeline": {
                "authority": authority,
                "source_health": source_events,
                "opportunities": opportunities,
            },
            "coverage_gaps": coverage_gaps,
            "delays_and_service_misses": delay_records,
            "false_alarms": {
                "assessment_state": "not_assessed_without_ground_truth",
                "items": [],
            },
            "misses": {
                "assessment_state": "not_assessed_without_ground_truth",
                "items": [],
            },
            "unresolved_actions": unresolved,
            "operator_comments": operator_comments,
            "corrective_actions": [],
            "notifications": notifications,
            "referenced_artifacts": [],
        }
        review["review_content_sha256"] = sha256_bytes(canonical_json_bytes(review))
        return review

    def verify(self, review: dict[str, Any]) -> bool:
        claimed = review.get("review_content_sha256")
        payload = dict(review)
        payload.pop("review_content_sha256", None)
        return isinstance(claimed, str) and claimed == sha256_bytes(canonical_json_bytes(payload))

    def write(
        self,
        engine: Any,
        scenario_result: Any,
        store: ContentAddressedArtifactStore,
    ) -> ArtifactRef:
        review = self.build(engine, scenario_result)
        return store.put_bytes(
            canonical_json_bytes(review), media_type="application/json",
            policy=ArtifactPolicy.after_event_review(),
            scope=ArtifactScope(scenario_run_id=str(review.get("scenario_id", "after-event-review"))),
        )
