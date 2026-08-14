import pytest

from sentinel_edge.qualification.cpu_ep import CpuExecutionPathComparison


def test_cpu_ep_comparison_retains_build_log_and_control_ablation() -> None:
    result = CpuExecutionPathComparison(path_id="cpu-ep-kleidiai-v1", build_command="python build.py --kleidiai",
        build_log_sha256="a" * 64, kleidiai_enabled=True, control_ablation_retained=True,
        control_log_sha256="b" * 64, comparison_metrics={"latency_ms": 12.0})
    assert result.control_ablation_retained is True
    assert result.build_command.endswith("--kleidiai")


def test_cpu_ep_requires_control_ablation() -> None:
    with pytest.raises(ValueError):
        CpuExecutionPathComparison(path_id="cpu", build_command="build", build_log_sha256="a" * 64,
            kleidiai_enabled=True, control_ablation_retained=False, control_log_sha256="b" * 64,
            comparison_metrics={"latency_ms": 1.0})
