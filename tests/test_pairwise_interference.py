import pytest

from sentinel_edge.benchmark import measure_pairwise_interference


def test_pairwise_interference_stores_p99_inflation_and_memory_delta() -> None:
    report = measure_pairwise_interference(
        hero_workload="earthquake-trigger",
        co_runner="wildfire-stage2",
        solo_latency_ms=[10, 12, 15],
        co_run_latency_ms=[12, 18, 24],
        solo_memory_mb=[32, 34],
        co_run_memory_mb=[40, 44],
        declared_co_runners=["wildfire-stage2"],
    )
    assert report.p99_inflation_ratio == 1.6
    assert report.memory_delta_mb == 10
    assert report.solo_sample_count == report.co_run_sample_count == 3


def test_pairwise_interference_rejects_undeclared_co_runner() -> None:
    with pytest.raises(ValueError, match="declared"):
        measure_pairwise_interference(
            hero_workload="earthquake-trigger", co_runner="unknown",
            solo_latency_ms=[1], co_run_latency_ms=[2],
            solo_memory_mb=[1], co_run_memory_mb=[2], declared_co_runners=[],
        )
