import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sentinel_edge.domain.models import (
    BenchmarkVariant,
    ClaimClass,
    HostObservation,
    HostQualificationReport,
    CapabilityState,
    RuntimeMode,
)
from sentinel_edge.qualification import (
    build_development_benchmark_evidence,
    commission_imu,
    evaluate_readiness,
    load_host_profile,
    load_runtime_profile,
    qualify_host,
    qualify_runtime_profile,
    validate_benchmark_evidence,
)
from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file


def _matching_host() -> HostObservation:
    return HostObservation(
        observed_at=datetime(2026, 8, 2, tzinfo=timezone.utc),
        system="Linux",
        machine="aarch64",
        kernel_release="6.12.0-test",
        os_id="debian",
        os_version_id="13",
        board_model="Raspberry Pi 5 Model B Rev 1.0",
        cpu_model="Cortex-A76",
        cpu_count=4,
        memory_mb=4096,
        architecture_64bit=True,
        psi_available=True,
        cgroup_v2=True,
        thermal_sensor_count=1,
        maximum_temperature_c=55.0,
        power_evidence="throttled=0x0",
        boot_id_sha256="a" * 64,
        observed_files={},
    )


def test_host_qualification_separates_observation_from_target_match() -> None:
    profile = load_host_profile("fixtures/qualification/raspberry-pi-5-h0.json")
    report = qualify_host(profile, _matching_host())
    assert report.state is CapabilityState.TARGET_QUALIFIED
    assert report.host_profile_match is True
    assert report.target_device_claim_allowed is True

    rejected = qualify_host(profile, _matching_host().model_copy(update={"machine": "x86_64"}))
    assert rejected.state is CapabilityState.FAILED
    assert rejected.target_device_claim_allowed is False
    assert "architecture_mismatch" in rejected.reason_codes


def test_imu_fixture_can_pass_signal_quality_without_proving_physical_device() -> None:
    report = commission_imu(
        "fixtures/sensors/imu-100hz-development.jsonl",
        source_id="imu-development",
        requested_rate_hz=100.0,
    )
    assert report.state is CapabilityState.TESTED
    assert report.physical_source_proven is False
    assert report.sample_count == 200
    assert report.sequence_gaps == 0
    assert report.non_monotonic_samples == 0
    assert "physical_device_not_proven" in report.reason_codes


def test_imu_commissioning_rejects_clock_and_sequence_defects(tmp_path: Path) -> None:
    source = tmp_path / "bad.jsonl"
    rows = [
        {"sequence": 0, "monotonic_ns": 100, "x": 0, "y": 0, "z": 9.8, "unit": "m/s2"},
        {"sequence": 2, "monotonic_ns": 100, "x": 0, "y": 0, "z": 9.8, "unit": "m/s2"},
    ]
    source.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    report = commission_imu(source, source_id="bad", requested_rate_hz=100.0, minimum_samples=2)
    assert report.state is CapabilityState.FAILED
    assert "non_monotonic_sampling_clock" in report.reason_codes
    assert "sequence_gaps" in report.reason_codes


def test_runtime_profile_is_development_only_without_bound_target_host() -> None:
    manifest = load_runtime_profile("fixtures/runtime/seismic-trigger-v1.profile.json")
    report = qualify_runtime_profile(manifest, root=".", now=datetime(2026, 8, 3, tzinfo=timezone.utc))
    assert report.state is CapabilityState.TESTED
    assert report.model_integrity_match is True
    assert report.runtime_identity_match is True
    assert report.quality_evidence_complete is True
    assert report.benchmark_evidence_complete is True
    assert report.target_qualified is False
    assert report.release_admissible is False


def test_runtime_profile_rejects_model_digest_tamper(tmp_path: Path) -> None:
    manifest = load_runtime_profile("fixtures/runtime/seismic-trigger-v1.profile.json")
    copied = tmp_path / "root"
    copied.mkdir()
    model = copied / manifest.model_path
    model.parent.mkdir(parents=True)
    model.write_text("tampered")
    for binding in (*manifest.quality_evidence, *manifest.benchmark_evidence):
        target = copied / binding.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((Path(binding.path)).read_text())
    report = qualify_runtime_profile(manifest, root=copied, now=datetime(2026, 8, 3, tzinfo=timezone.utc))
    assert report.state is CapabilityState.FAILED
    assert "model_digest_mismatch" in report.reason_codes


def test_benchmark_validator_refuses_development_placeholder_as_target_measurement(tmp_path: Path) -> None:
    host_path = tmp_path / "host.json"
    host_path.write_text(qualify_host(load_host_profile("fixtures/qualification/raspberry-pi-5-h0.json"), _matching_host()).model_dump_json())
    payload = build_development_benchmark_evidence(
        benchmark_id="development",
        benchmark_manifest_path="fixtures/scenarios/benchmark-open-loop.json",
        host_report_path=host_path,
    )
    path = tmp_path / "benchmark.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    report = validate_benchmark_evidence(path)
    assert report.source_class is ClaimClass.SIMULATED
    assert report.target_measurement_claim_allowed is False
    assert set(report.variants) == set(BenchmarkVariant)
    assert "source_not_measured" in report.reason_codes


def test_benchmark_validator_accepts_only_complete_target_evidence(tmp_path: Path) -> None:
    payload = {
        "schema": "sentinel-edge-target-benchmark-evidence/1.0",
        "benchmark_id": "target-pass",
        "benchmark_manifest_sha256": "a" * 64,
        "host_report_sha256": "b" * 64,
        "runtime_profile_sha256s": ["c" * 64],
        "source_class": "measured",
        "variants": [variant.value for variant in BenchmarkVariant],
        "quality_guardrails_passed": True,
        "thermal_valid": True,
        "power_valid": True,
        "target_host_qualified": True,
        "samples": [
            {"variant": variant.value, "opportunity_manifest_sha256": "d" * 64, "elapsed_ms": 1.0}
            for variant in BenchmarkVariant
        ],
    }
    path = tmp_path / "target.json"
    path.write_text(json.dumps(payload))
    report = validate_benchmark_evidence(path)
    assert report.target_measurement_claim_allowed is True
    assert report.reason_codes == ("target_benchmark_evidence_valid",)


def test_readiness_barrier_blocks_missing_critical_qualification() -> None:
    report = evaluate_readiness(
        mode=RuntimeMode.BENCHMARK,
        active_configuration=True,
        incident_authority_available=True,
        artifact_store_writable=True,
        schema_compatible=True,
        clock_usable=True,
        minimum_coverage=True,
        recovery_reconciled=True,
        profile_ids_required={"a", "b"},
        profile_ids_admitted={"a"},
        physical_signal_required=True,
        physical_signal_qualified=False,
        target_host_required=True,
        target_host_qualified=False,
    )
    assert report.state.value == "blocked"
    assert "runtime_profiles_complete" in report.reason_codes
    assert "physical_signal_qualified" in report.reason_codes
    assert "target_host_qualified" in report.reason_codes
