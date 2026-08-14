from sentinel_edge.qualification.exposure import ExposureEstimate, HazardVerification, ReviewPriorityRule, VerificationState, combine_exposure_and_verification


def test_high_exposure_does_not_promote_hazard_verification_state() -> None:
    result = combine_exposure_and_verification(
        ExposureEstimate(estimated_population=100000, estimated_buildings=5000, source_version="ghsl-v1"),
        HazardVerification(VerificationState.UNVERIFIED, 0.1),
    )
    assert result["review_priority"] == "high"
    assert result["verification"].state is VerificationState.UNVERIFIED
    assert result["exposure"].estimated_population == 100000
    wording = result["exposure"].wording().lower()
    assert "estimated potential exposure" in wording
    assert "affected" not in wording and "killed" not in wording and "casualt" not in wording


def test_review_priority_is_versioned_bounded_and_keeps_monitoring_cadence() -> None:
    result = combine_exposure_and_verification(
        ExposureEstimate(estimated_population=2000), HazardVerification(VerificationState.SUSPECTED, 0.4),
        ReviewPriorityRule(version="exposure-priority-v2", priority_duration_seconds=120),
    )
    assert result["review_priority"] == "high"
    assert result["priority_reason"] == "potential_exposure_threshold"
    assert result["priority_rule_version"] == "exposure-priority-v2"
    assert result["priority_duration_seconds"] == 120
    assert result["monitoring_cadence_seconds"] == 60
    assert result["verification"].state is VerificationState.SUSPECTED
