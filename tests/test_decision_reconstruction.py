from sentinel_edge.review.decision_reconstruction import DecisionReconstruction


def test_original_and_current_decision_contexts_are_separate() -> None:
    record = DecisionReconstruction("d1", {"source_version": "v1", "state": "suspected"}, {"source_version": "v2", "state": "confirmed"}, "suspected", "confirmed")
    view = record.as_audit_view()
    assert view["original_decision"]["context"]["source_version"] == "v1"
    assert view["current_reevaluation"]["context"]["source_version"] == "v2"
    assert view["historical_context_rewritten"] is False
