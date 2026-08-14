import pytest

from sentinel_edge.qualification.host_variability import HostVariabilityReport, IsolationAblationEvidence


def test_host_variability_retains_paired_blocks_and_noise_findings() -> None:
    report = HostVariabilityReport(boot_to_boot_ms=(120.0, 125.0), block_to_block_ms=(10.0, 11.0),
        paired_blocks=2, host_noise_findings=("scheduler_jitter",))
    assert report.paired_blocks == 2
    assert "scheduler_jitter" in report.host_noise_findings


def test_isolation_requires_before_measurement_and_control_ablation() -> None:
    evidence = IsolationAblationEvidence(profile_id="isolated-v1", measured_before=True,
        control_ablation_retained=True, pinned_processes=("worker",), pinned_irqs=("irq1",))
    assert evidence.measured_before is True
    with pytest.raises(ValueError):
        IsolationAblationEvidence(profile_id="isolated-v1", measured_before=False,
            control_ablation_retained=True, pinned_processes=("worker",))
