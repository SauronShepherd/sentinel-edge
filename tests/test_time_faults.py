from sentinel_edge.qualification.time_faults import FAULTS, evaluate_time_fault


def test_all_time_faults_have_deterministic_safe_outcomes_and_reason_codes() -> None:
    outcomes = [evaluate_time_fault(fault) for fault in FAULTS]
    assert all(item.safe and item.reason_code for item in outcomes)
