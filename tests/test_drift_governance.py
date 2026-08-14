from sentinel_edge.qualification.drift import DriftAction, DriftBaseline, DriftKind, DriftObservation, evaluate_drift


def baseline() -> DriftBaseline:
    return DriftBaseline("wildfire", "site-a", "camera-v1", "smoke-v2", "fixture-v1", "summer", "operator-v1")


def test_short_or_single_window_drift_preserves_profile() -> None:
    result = evaluate_drift(DriftObservation(baseline(), DriftKind.PREVALENCE, 2, 10, 0.1, 1))
    assert result.action is DriftAction.PRESERVE
    assert result.automatic_retraining_allowed is False


def test_drift_is_dimension_bound_and_cannot_strengthen_incident_confidence() -> None:
    result = evaluate_drift(DriftObservation(baseline(), DriftKind.SENSOR, 100, 1000, 0.1, 4))
    assert result.action is DriftAction.WEAKEN
    assert "incident_confidence_not_strengthened" in result.reason_codes


def test_unproven_cause_requires_review() -> None:
    result = evaluate_drift(DriftObservation(baseline(), DriftKind.UPSTREAM, 100, 1000, 0.1, 4, evidence=False))
    assert result.action is DriftAction.REVIEW_REQUIRED
