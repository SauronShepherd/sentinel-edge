import pytest

from sentinel_edge.storage.telemetry_budget import TelemetryBudgetReport


def test_telemetry_budget_report_passes_clean_stress_and_privacy_corpus() -> None:
    report = TelemetryBudgetReport(unique_series=10, maximum_series=100, peak_memory_bytes=1000,
        maximum_memory_bytes=2000, leak_corpus_checked=50, leak_matches=0, stress_passed=True)
    assert report.leak_matches == 0


def test_telemetry_budget_rejects_cardinality_or_leak_failure() -> None:
    with pytest.raises(ValueError):
        TelemetryBudgetReport(unique_series=101, maximum_series=100, peak_memory_bytes=1,
            maximum_memory_bytes=2, leak_corpus_checked=1, leak_matches=0, stress_passed=True)
    with pytest.raises(ValueError):
        TelemetryBudgetReport(unique_series=1, maximum_series=100, peak_memory_bytes=1,
            maximum_memory_bytes=2, leak_corpus_checked=1, leak_matches=1, stress_passed=True)
