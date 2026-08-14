from sentinel_edge.benchmark import DeterministicBenchmarkLab, load_benchmark_manifest
from sentinel_edge.domain.models import BenchmarkVariant, ClaimClass


def test_open_loop_benchmark_is_deterministic_and_truthfully_simulated() -> None:
    manifest = load_benchmark_manifest("fixtures/scenarios/benchmark-open-loop.json")
    lab = DeterministicBenchmarkLab()
    first = {variant: lab.run(manifest, variant) for variant in BenchmarkVariant}
    second = {variant: lab.run(manifest, variant) for variant in BenchmarkVariant}
    assert first == second
    assert manifest["benchmark_policy"]["arrival_mode"] == "open_loop"
    assert len({run.schedule_digest for run in first.values()}) == 1
    assert len({run.instrumentation_config_hashes for run in first.values()}) == 1
    assert len({run.telemetry_policy_digest for run in first.values()}) == 1
    import json
    assert len({json.dumps(run.camera_preprocessing, sort_keys=True) for run in first.values()}) == 1
    assert all(run.claim_class is ClaimClass.SIMULATED for run in first.values())
    assert all(run.offered == run.processed + run.skipped for run in first.values())
    for run in first.values():
        assert run.opportunity_accounting["offered"] == run.offered
        assert run.opportunity_accounting["processed"] == run.processed
        assert run.opportunity_accounting["skipped"] == run.skipped
        assert {"dropped", "replaced", "never_started", "expired", "deadline_missed"} <= run.opportunity_accounting.keys()
    for run in first.values():
        assert run.latency_histogram["range_policy"] == "overflow_not_clipped"
        assert run.p50_end_to_end_ms <= run.p95_end_to_end_ms <= run.p99_end_to_end_ms
        assert len(run.raw_latency_samples_ms) == run.processed
        assert sum(run.latency_histogram["counts"]) + run.latency_overflow_count == run.processed
        assert {"model_size_bytes", "rss_mb", "cpu_pressure", "temperature_c"} <= run.resource_samples[0].keys()
        assert run.resource_samples[0]["source"] == "simulated_benchmark_resource_snapshot"
        assert run.resource_samples[0]["evidence_class"] == "simulated"
        assert run.resource_samples[0]["physical_measurement"] is False
        assert run.total_service_ms > 0
        assert run.total_queue_delay_ms >= 0
        assert 0.0 <= run.heavy_model_duty_cycle <= 1.0
        assert run.heavy_model_invocation_count == sum(
            1 for record in run.records
            if record["disposition"] == "processed" and record["workload_id"] in manifest["heavy_workload_ids"]
        )
        assert run.heavy_model_service_ms == sum(
            int(record["service_ms"] or 0) for record in run.records
            if record["disposition"] == "processed" and record["workload_id"] in manifest["heavy_workload_ids"]
        )
        assert {"flood", "earthquake", "wildfire", "landslide"} <= run.hazard_quality.keys()
        assert all("completion_rate" in row for row in run.hazard_quality.values())
        processed = next(item for item in run.records if item["disposition"] == "processed")
        assert sum(processed["stage_latency_ms"].values()) == processed["service_ms"]
    b0_quake = next(record for record in first[BenchmarkVariant.B0].records if record["hazard"] == "earthquake")
    o1_quake = next(record for record in first[BenchmarkVariant.O1].records if record["hazard"] == "earthquake")
    assert o1_quake["completion_ms"] < b0_quake["completion_ms"]
    opportunity = next(item for item in manifest["opportunities"] if item["opportunity_key"] == b0_quake["opportunity_key"])
    assert b0_quake["service_ms"] == opportunity["service_ms"]["B0"]
    b1_quake = next(record for record in first[BenchmarkVariant.B1].records if record["opportunity_key"] == b0_quake["opportunity_key"])
    assert b1_quake["service_ms"] == opportunity["service_ms"]["B1"]
    assert first[BenchmarkVariant.B0].execution_mode == first[BenchmarkVariant.B1].execution_mode == "fixed_rate"
    assert first[BenchmarkVariant.B0].schedule_digest == first[BenchmarkVariant.B1].schedule_digest == first[BenchmarkVariant.O1].schedule_digest
    o1_bench = next(record for record in first[BenchmarkVariant.O1].records if record["opportunity_key"] == b0_quake["opportunity_key"])
    assert o1_bench["service_ms"] == opportunity["service_ms"]["O1"]
    assert first[BenchmarkVariant.O1].execution_mode == "orchestrated"
    assert first[BenchmarkVariant.O1].quality_scope == "timed_run_only"
    assert first[BenchmarkVariant.O1].scheduler_decision_count > 0
    assert first[BenchmarkVariant.B0].scheduler_decision_count == 0
    assert first[BenchmarkVariant.B1].scheduler_decision_count == 0
    for variant in BenchmarkVariant:
        observed = {row["opportunity_key"]: row["capture_ms"] for row in first[variant].records}
        expected = {row["opportunity_key"]: row["captured_offset_ms"] for row in manifest["opportunities"]}
        assert observed == expected


def test_closed_loop_manifest_is_rejected() -> None:
    manifest = load_benchmark_manifest("fixtures/scenarios/benchmark-open-loop.json")
    manifest["benchmark_policy"] = {"arrival_mode": "closed_loop"}
    import pytest
    with pytest.raises(ValueError, match="open_loop"):
        DeterministicBenchmarkLab().run(manifest, BenchmarkVariant.B0)


def test_scheduler_overhead_microbenchmark_is_explicitly_emulator_scoped() -> None:
    from scripts.run_emulated_benchmark import measure_scheduler_overhead

    manifest = load_benchmark_manifest("fixtures/scenarios/benchmark-open-loop.json")
    result = measure_scheduler_overhead(manifest, iterations=2)
    assert result["measurement_class"] == "measured_emulated_arm64"
    assert result["scope"] == "component_3_scheduler_python_control_plane"
    assert result["iterations"] == 2
    assert result["decision_count"] > 0
    assert result["total_cpu_ms"] >= 0
    assert result["median_per_decision_us"] >= 0
    assert "not Raspberry Pi 5" in result["note"]
