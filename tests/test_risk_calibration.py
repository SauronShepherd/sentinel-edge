from sentinel_edge.qualification.risk_calibration import RiskCalibrationReport


def test_subgroup_failures_are_not_hidden_by_entropy_shift() -> None:
    report = RiskCalibrationReport(0.2, 1.0, 0.0, 0.9, {"low-light": {"recall": 0.5, "false_alert_rate": 0.0}})
    assert "subgroup_recall_failed:low-light" in report.failures()
