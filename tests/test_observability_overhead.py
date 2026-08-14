import pytest

from sentinel_edge.qualification.observability import ObservabilityOverheadReport


def test_observability_ablation_reports_cpu_io_latency_perturbation() -> None:
    report = ObservabilityOverheadReport(baseline_cpu_percent=10, diagnostic_cpu_percent=12,
        baseline_io_bytes=100, diagnostic_io_bytes=180, baseline_latency_ms=20, diagnostic_latency_ms=23,
        ablation_id="diag-off-v1", cpu_perturbation_percent=2, io_perturbation_bytes=80,
        latency_perturbation_ms=3)
    assert report.cpu_perturbation_percent == 2
    assert report.io_perturbation_bytes == 80
    assert report.latency_perturbation_ms == 3


def test_observability_measurements_cannot_claim_inconsistent_perturbation() -> None:
    with pytest.raises(ValueError):
        ObservabilityOverheadReport(baseline_cpu_percent=10, diagnostic_cpu_percent=12,
            baseline_io_bytes=100, diagnostic_io_bytes=180, baseline_latency_ms=20, diagnostic_latency_ms=23,
            ablation_id="diag-off-v1", cpu_perturbation_percent=0, io_perturbation_bytes=80,
            latency_perturbation_ms=3)
