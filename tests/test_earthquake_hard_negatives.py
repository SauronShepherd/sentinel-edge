from sentinel_edge.qualification import HardNegativeKind, build_hard_negative_report


def test_handling_footsteps_and_traffic_hard_negative_report() -> None:
    report = build_hard_negative_report()
    assert report.passed is True
    assert report.classification == "simulated"
    assert {case.kind for case in report.cases} == {
        HardNegativeKind.HANDLING, HardNegativeKind.FOOTSTEPS, HardNegativeKind.TRAFFIC,
    }
    assert all(case.expected_nonseismic and case.passed for case in report.cases)


def test_hard_negative_report_exposes_a_failed_case() -> None:
    report = build_hard_negative_report(((HardNegativeKind.TRAFFIC, "traffic-high", 1.0),))
    assert report.passed is False
    assert report.failure_count == 1
    assert report.cases[0].classifier_label == "earthquake-like"
