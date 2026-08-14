from sentinel_edge.qualification.drift_campaign import SCENARIOS, evaluate_drift_scenario


def test_drift_campaign_has_safe_limited_outcomes_for_all_scenarios() -> None:
    results = [evaluate_drift_scenario(item) for item in SCENARIOS]
    assert all(item.safe_action == "review_and_abstain" and item.synthetic_only for item in results)
