"""Human-readable escalation and non-escalation reasons for analysis results."""
from __future__ import annotations

from sentinel_edge.domain.models import AnalysisResult, IncidentState


def build_decision_trace(result: AnalysisResult) -> dict[str, object]:
    blocking = sorted(code for code in result.reason_codes if any(
        marker in code for marker in ("insufficient", "abstention", "camera_", "stale", "missing", "uncertain", "rejected")
    ))
    positive = sorted(code for code in result.reason_codes if code not in blocking)
    if result.state_hint in {IncidentState.SUSPECTED, IncidentState.CONFIRMED}:
        outcome = "escalated"
    else:
        outcome = "not_escalated"
    if not positive and result.score > 0:
        positive = ["score_positive"]
    if not blocking and outcome == "not_escalated":
        blocking = ["threshold_not_reached"]
    return {
        "schema": "sentinel-edge-decision-trace/1.0",
        "outcome": outcome,
        "state": result.state_hint.value,
        "positive_reasons": positive,
        "blocking_reasons": blocking,
        "score": result.score,
        "abstained": result.abstained,
    }
