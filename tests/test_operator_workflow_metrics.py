from datetime import datetime, timezone
from uuid import uuid4

from sentinel_edge.domain.models import AnalysisResult, CoverageState, HazardKind, IncidentState, ReviewAction, ReviewActionKind
from sentinel_edge.incidents import IncidentEventEngine


def test_workflow_metrics_reports_acknowledgement_time() -> None:
    now = datetime(2026, 8, 12, 10, 0, tzinfo=timezone.utc)
    engine = IncidentEventEngine()
    incident = engine.apply_analysis(AnalysisResult(
        observation_id=uuid4(), hazard=HazardKind.WILDFIRE, score=0.7,
        state_hint=IncidentState.SUSPECTED, features={}, coverage=CoverageState.SUFFICIENT,
        produced_at=now,
    ), accepted_at=now)
    engine.review(ReviewAction(
        incident_id=incident.incident_id, hazard=incident.hazard,
        action=ReviewActionKind.ACKNOWLEDGE, actor="operator", created_at=now.replace(second=5),
    ))
    metrics = engine.workflow_metrics()
    assert metrics["schema"] == "sentinel-edge-operator-workflow-metrics/1.0"
    assert metrics["acknowledgement_time_seconds"] == [5.0]
    assert metrics["acknowledged_count"] == 1
