from __future__ import annotations

import json
import os
import platform
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from packaging.tags import sys_tags

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sentinel_edge.benchmark import (
    BenchmarkAnalysisPlan,
    BenchmarkExecutionRecord,
    BenchmarkIdentitySet,
    BenchmarkSample,
    FileIdentitySpec,
    analyze_execution,
    sign_analysis_plan,
    verify_file_identities,
)
from sentinel_edge.domain.models import BenchmarkVariant, ClaimClass, HostQualificationReport, HazardKind, SensorKind
from sentinel_edge.qualification import (
    load_runtime_profile,
    qualify_runtime_profile,
    run_isolated_benchmark_command,
    write_host_trust_report,
    write_network_isolation_report,
    EnergyEvidenceKind,
    EnergyMeasurement,
    PowerHealthMonitor,
    PowerTelemetrySample,
    evaluate_energy_comparison,
    RuntimeIssueContext,
    RuntimeIssueDisposition,
    RuntimeIssueMatch,
    RuntimeKnownIssue,
    RuntimeKnownIssueRegistry,
    evaluate_runtime_known_issues,
    sign_runtime_issue_registry,
    AntiAliasFilter,
    RateOperation,
    RateOperationKind,
    SignalChainObservation,
    SignalChainProfile,
    SignalSourceClass,
    SiteCommissioningRecord,
    evaluate_signal_chain,
    evaluate_site_commissioning,
    sign_signal_chain_profile,
    sign_site_commissioning_record,
)
from sentinel_edge.release import (
    AdvisoryCoveragePolicy,
    apply_coverage_policy,
    build_attestation,
    build_independent_build_report,
    build_release_governance_report,
    build_security_review,
    mirror_installed_resolution,
    scan_toolchain_inventory,
    verify_target_wheelhouse,
    verify_wheelhouse,
    write_cyclonedx_sbom,
    write_independent_build_report,
    write_release_governance_report,
    write_release_lock,
    write_reproducibility_report,
    write_third_party_inventory,
    write_third_party_notices,
)
from sentinel_edge.release.advisories import load_advisory_snapshot
from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file
from sentinel_edge.update import key_id
from sentinel_edge.runtime import (
    DimensionBound,
    ModelPackageManifest,
    PackageFile,
    RuntimeAdmissionContext,
    TensorAllocationContract,
    admit_model_package,
    scan_model_execution_boundaries,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_public(path: Path, key: Ed25519PrivateKey) -> None:
    path.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))


def _copy_evidence(name: str, source: Path) -> None:
    shutil.copy2(source, ROOT / "evidence" / f"v0.20.0-{name}")


def _varint(value: int) -> bytes:
    result = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            result.append(byte | 0x80)
        else:
            result.append(byte)
            return bytes(result)


def _field_varint(number: int, value: int) -> bytes:
    return _varint((number << 3) | 0) + _varint(value)


def _field_bytes(number: int, value: bytes) -> bytes:
    return _varint((number << 3) | 2) + _varint(len(value)) + value


def _field_text(number: int, value: str) -> bytes:
    return _field_bytes(number, value.encode("utf-8"))


def _dimension(value: int | str) -> bytes:
    return _field_varint(1, value) if isinstance(value, int) else _field_text(2, value)


def _value_info(name: str, dtype: int, dimensions: tuple[int | str, ...]) -> bytes:
    shape = b"".join(_field_bytes(1, _dimension(item)) for item in dimensions)
    tensor_type = _field_varint(1, dtype) + _field_bytes(2, shape)
    return _field_text(1, name) + _field_bytes(2, _field_bytes(1, tensor_type))


def _node(operator: str, *, attribute_name: str | None = None) -> bytes:
    payload = _field_text(4, operator)
    if attribute_name:
        attribute = _field_text(1, attribute_name) + _field_varint(3, 1) + _field_varint(20, 2)
        payload += _field_bytes(5, attribute)
    return payload


def _tensor(name: str, dimensions: tuple[int, ...]) -> bytes:
    payload = b"".join(_field_varint(1, item) for item in dimensions)
    payload += _field_varint(2, 1) + _field_text(8, name)
    payload += _field_bytes(9, b"\x00" * (4 * max(1, dimensions[0] * dimensions[-1])))
    return payload


def _development_onnx() -> bytes:
    graph = _field_bytes(1, _node("MatMul")) + _field_bytes(1, _node("Sigmoid", attribute_name="fixture"))
    graph += _field_bytes(5, _tensor("weight", (3, 1)))
    graph += _field_bytes(11, _value_info("features", 1, ("N", 3)))
    graph += _field_bytes(12, _value_info("score", 1, ("N", 1)))
    opset = _field_text(1, "") + _field_varint(2, 18)
    return _field_varint(1, 9) + _field_bytes(7, graph) + _field_bytes(8, opset)


def build() -> dict:
    evidence = ROOT / "evidence"
    evidence.mkdir(exist_ok=True)

    lock_path = write_release_lock(ROOT, ROOT / "requirements-release.lock.json")
    wheelhouse = ROOT / "artifacts" / "wheelhouse"
    wheelhouse.mkdir(parents=True, exist_ok=True)
    for old in wheelhouse.glob("*.whl"):
        old.unlink()
    capture = mirror_installed_resolution(lock_path, wheelhouse)
    current_wheel_report = verify_wheelhouse(
        lock_path,
        wheelhouse,
        compatible_tags={str(tag) for tag in sys_tags()},
        install_rehearsal=True,
    )
    _write_json(ROOT / "wheelhouse-report.json", current_wheel_report)

    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    target_manifest = {
        "schema": "sentinel-edge-target-wheel-acquisition/1.0",
        "target_platform": "linux-aarch64-raspberry-pi-5",
        "entries": [
            {
                "name": item["name"],
                "version": item["version"],
                "path": "",
                "sha256": None,
                "bytes": None,
                "origin_kind": "publisher_index",
                "origin_url": None,
                "publisher_origin_proven": False,
                "tags": ["cp313-cp313-manylinux_2_28_aarch64", "py3-none-any"],
            }
            for item in lock.get("resolved", [])
            if item.get("state") == "resolved"
        ],
        "installation_rehearsal": {
            "success": False,
            "no_index": True,
            "require_hashes": True,
            "machine": "aarch64",
            "installed_lock_sha256": sha256_file(lock_path),
            "reason": "publisher-origin Arm64 wheels and qualified Raspberry Pi image not available in this environment",
        },
    }
    target_manifest_path = ROOT / "fixtures/release/arm64-target-wheel-acquisition-v0.20.0.json"
    _write_json(target_manifest_path, target_manifest)
    target_wheel_report = verify_target_wheelhouse(
        lock_path,
        target_manifest_path,
        root=ROOT,
        required_target_tags=("cp313-cp313-manylinux_2_28_aarch64", "py3-none-any"),
    )
    _write_json(ROOT / "target-wheelhouse-report.json", target_wheel_report)

    network_path = write_network_isolation_report(ROOT / "network-isolation-report.json")
    isolated = run_isolated_benchmark_command([
        sys.executable,
        "-c",
        "import os; assert os.environ.get('SENTINEL_BENCHMARK_NETWORK_ISOLATED') == '1'; print('benchmark-workload-ok')",
    ])
    _write_json(ROOT / "qualification/isolated-benchmark-command.json", isolated)

    host_report = json.loads((ROOT / "qualification/host-qualification.json").read_text(encoding="utf-8"))
    runtime_manifest = load_runtime_profile(ROOT / "fixtures/runtime/seismic-trigger-v1.profile.json")
    runtime_report_model = qualify_runtime_profile(
        runtime_manifest,
        root=ROOT,
        host_report=HostQualificationReport.model_validate(host_report),
    )
    runtime_report = runtime_report_model.model_dump(mode="json")
    _write_json(ROOT / "qualification/runtime-profile-qualification.json", runtime_report)

    network_report = json.loads(network_path.read_text(encoding="utf-8"))
    model_path = ROOT / runtime_manifest.model_path
    config_path = ROOT / "fixtures/configuration/default-v0.20.0.yaml"
    fixture_path = ROOT / "fixtures/scenarios/benchmark-open-loop.json"
    runtime_digest = sha256_bytes(canonical_json_bytes(runtime_report))
    identity_set = BenchmarkIdentitySet(
        runtime_profile_sha256s=(runtime_digest,),
        model_sha256s=(sha256_file(model_path),),
        configuration_sha256=sha256_file(config_path),
        fixture_manifest_sha256=sha256_file(fixture_path),
        opportunity_manifest_sha256=sha256_file(fixture_path),
        host_report_sha256=sha256_bytes(canonical_json_bytes(host_report)),
        network_isolation_report_sha256=network_report["report_digest"],
        wheelhouse_report_sha256=target_wheel_report["report_digest"],
    )
    identity_specs = (
        FileIdentitySpec(name="runtime_profile", path="fixtures/runtime/seismic-trigger-v1.profile.json", sha256=sha256_file(ROOT / "fixtures/runtime/seismic-trigger-v1.profile.json")),
        FileIdentitySpec(name="model", path=runtime_manifest.model_path, sha256=sha256_file(model_path)),
        FileIdentitySpec(name="configuration", path="fixtures/configuration/default-v0.20.0.yaml", sha256=sha256_file(config_path)),
        FileIdentitySpec(name="fixture", path="fixtures/scenarios/benchmark-open-loop.json", sha256=sha256_file(fixture_path)),
    )
    identity_spec_payload = {"schema": "sentinel-edge-benchmark-identity-spec/1.0", "items": [item.model_dump(mode="json") for item in identity_specs]}
    _write_json(ROOT / "fixtures/benchmark/v0.20.0-identity-spec.json", identity_spec_payload)
    identity_report = verify_file_identities(ROOT, identity_specs)
    _write_json(ROOT / "qualification/benchmark-identity-report.json", identity_report)

    plan = BenchmarkAnalysisPlan(
        plan_id="sentinel-edge-v0.20.0-confirmatory-development-envelope",
        created_at=datetime(2026, 8, 3, 7, 0, tzinfo=timezone.utc),
        claim_set="confirmatory",
        primary_metrics=("end_to_end_ms", "work_proxy_units"),
        guardrails={"max_deadline_miss_rate": 0.01, "minimum_quality_recall": 0.90, "max_memory_psi_avg10": 0.5, "max_major_faults_delta": 0},
        exclusions=("thermal_invalid", "power_invalid", "host_noise_invalid", "identity_mismatch", "network_attempt"),
        confidence_level=0.95,
        bootstrap_resamples=1000,
        variants=(BenchmarkVariant.B0, BenchmarkVariant.B1, BenchmarkVariant.O1),
        minimum_complete_pairs=3,
        stop_rule={"type": "fixed_complete_pairs", "count": 3},
        offered_load_manifest_sha256=identity_set.opportunity_manifest_sha256,
        identities=identity_set,
    )
    plan_key = Ed25519PrivateKey.generate()
    signed_plan = sign_analysis_plan(plan, plan_key, signed_at=datetime(2026, 8, 3, 7, 1, tzinfo=timezone.utc))
    _write_public(evidence / "v0.20.0-benchmark-plan-public.pem", plan_key)
    _write_json(ROOT / "fixtures/benchmark/v0.20.0-signed-analysis-plan.json", signed_plan.model_dump(mode="json"))

    sample_values = {
        "pair-1": ((100.0, 8.0), (82.0, 7.0), (72.0, 6.5)),
        "pair-2": ((110.0, 8.5), (88.0, 7.3), (75.0, 6.8)),
        "pair-3": ((105.0, 8.2), (85.0, 7.1), (73.0, 6.6)),
    }
    samples = []
    block = 0
    for pair_id, values in sample_values.items():
        for variant, metrics in zip(BenchmarkVariant, values):
            samples.append(BenchmarkSample(
                block_index=block,
                pair_id=pair_id,
                opportunity_key=pair_id,
                variant=variant,
                metrics={"end_to_end_ms": metrics[0], "work_proxy_units": metrics[1]},
                platform=PowerTelemetrySample(
                    observed_at=datetime(2026, 8, 3, 7, 5, tzinfo=timezone.utc),
                    temperature_c=51.0 + block * 0.2,
                    under_voltage_current=False,
                    under_voltage_history=True,
                    frequency_capped_current=False,
                    frequency_capped_history=False,
                    throttled_current=False,
                    throttled_history=False,
                    swap_total_mb=0.0,
                    swap_used_mb=0.0,
                    zram_used_mb=0.0,
                    major_faults_delta=0,
                    memory_psi_avg10=0.0,
                    source="development-fixture",
                ),
                energy=EnergyMeasurement(
                    kind=EnergyEvidenceKind.PROXY,
                    source_class="simulated",
                    scenario_window_id=pair_id,
                    method="deterministic-work-proxy",
                    quality_target_id="v0.20.0-development-quality-guardrail",
                    quality_guardrail_passed=True,
                    proxy_value=metrics[1],
                    proxy_unit="work_proxy_units",
                ),
            ))
            block += 1
    execution = BenchmarkExecutionRecord(
        run_id="v0.20.0-development-analysis-rehearsal",
        plan_sha256=signed_plan.plan_sha256,
        started_at=datetime(2026, 8, 3, 7, 5, tzinfo=timezone.utc),
        completed_at=datetime(2026, 8, 3, 7, 6, tzinfo=timezone.utc),
        source_class=ClaimClass.SIMULATED,
        identities=identity_set,
        observed_network_attempts=0,
        mutation_attempts=(),
        samples=tuple(samples),
        declared_target_run=False,
    )
    _write_json(ROOT / "fixtures/benchmark/v0.20.0-development-execution.json", execution.model_dump(mode="json"))
    analysis = analyze_execution(
        signed_plan,
        plan_key.public_key(),
        execution,
        network_report=network_report,
        host_report=host_report,
        runtime_qualifications=(runtime_report,),
        wheelhouse_report=target_wheel_report,
    )
    _write_json(ROOT / "benchmark-analysis-report.json", analysis)

    power_monitor = PowerHealthMonitor(required_recovery_samples=3)
    power_snapshots = [
        power_monitor.observe(PowerTelemetrySample(
            observed_at=datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc), temperature_c=54.0,
            under_voltage_current=True, under_voltage_history=True, source="development-fixture",
        )),
        power_monitor.observe(PowerTelemetrySample(
            observed_at=datetime(2026, 8, 3, 8, 0, 1, tzinfo=timezone.utc), temperature_c=53.5,
            under_voltage_history=True, source="development-fixture",
        )),
        power_monitor.observe(PowerTelemetrySample(
            observed_at=datetime(2026, 8, 3, 8, 0, 2, tzinfo=timezone.utc), temperature_c=53.0,
            under_voltage_history=True, source="development-fixture",
        )),
        power_monitor.observe(PowerTelemetrySample(
            observed_at=datetime(2026, 8, 3, 8, 0, 3, tzinfo=timezone.utc), temperature_c=52.5,
            under_voltage_history=True, source="development-fixture",
        )),
    ]
    proxy_energy = evaluate_energy_comparison(tuple(
        EnergyMeasurement(
            kind=EnergyEvidenceKind.PROXY, source_class="simulated", scenario_window_id=f"proxy-{index}",
            method="deterministic-work-proxy", quality_target_id="v0.20.0-development-quality-guardrail",
            quality_guardrail_passed=True, proxy_value=value, proxy_unit="work_proxy_units",
        ) for index, value in enumerate((8.0, 7.0, 6.5), 1)
    ))
    physical_fixture = evaluate_energy_comparison(tuple(
        EnergyMeasurement(
            kind=EnergyEvidenceKind.PHYSICAL, source_class="fixture", scenario_window_id=f"physical-fixture-{index}",
            method="external-inline-meter-fixture", quality_target_id="v0.20.0-development-quality-guardrail",
            quality_guardrail_passed=True, energy_j=value, sampling_hz=10.0, idle_energy_j=0.5, uncertainty_j=0.1,
            complete_node_scope=True, included_components=("node", "storage", "cooling"), instrument_id="fixture-meter",
        ) for index, value in enumerate((4.2, 3.9, 3.7), 1)
    ))
    power_base = {
        "schema": "sentinel-edge-power-energy-qualification/1.0",
        "power_snapshots": [item.model_dump(mode="json") for item in power_snapshots],
        "degraded_power_observed": power_snapshots[0].state.value == "degraded_power",
        "recovery_hysteresis_passed": power_snapshots[-1].state.value == "healthy",
        "current_history_separated": all(item.current is None or item.current.under_voltage_current != item.current.under_voltage_history for item in power_snapshots[1:]),
        "proxy_energy": proxy_energy,
        "physical_fixture": physical_fixture,
        "release_eligible": False,
        "target_qualified": False,
        "limitations": [
            "Power and energy inputs are deterministic development fixtures, not Raspberry Pi telemetry or physical meter traces.",
            "The physical-format fixture proves disclosure and validation semantics but is not reportable as measured energy.",
        ],
    }
    power_report = {**power_base, "report_digest": sha256_bytes(canonical_json_bytes(power_base))}
    _write_json(ROOT / "power-energy-report.json", power_report)

    issue_key = Ed25519PrivateKey.generate()
    issue_registry = RuntimeKnownIssueRegistry(
        registry_id="sentinel-edge-runtime-known-issues", version=1,
        reviewed_at=datetime(2026, 8, 3, 8, 5, tzinfo=timezone.utc),
        expires_at=datetime(2026, 9, 2, 8, 5, tzinfo=timezone.utc),
        issues=(RuntimeKnownIssue(
            issue_id="RKI-DEVELOPMENT-REFERENCE-001",
            title="Reference issue for an explicitly different graph digest",
            match=RuntimeIssueMatch(
                runtime_name="sentinel-edge", runtime_version="0.20.0", provider="CPUExecutionProvider",
                architecture=platform.machine(), graph_sha256="f" * 64,
            ),
            default_disposition=RuntimeIssueDisposition.DENY,
            evidence_refs=("tests/test_runtime_known_issues_v020.py",),
            introduced_at=datetime(2026, 8, 2, 8, 5, tzinfo=timezone.utc),
            reviewed_at=datetime(2026, 8, 3, 8, 5, tzinfo=timezone.utc),
            expires_at=datetime(2026, 9, 2, 8, 5, tzinfo=timezone.utc),
        ),),
    )
    signed_issue_registry = sign_runtime_issue_registry(
        issue_registry, issue_key, signed_at=datetime(2026, 8, 3, 8, 5, 1, tzinfo=timezone.utc)
    )
    _write_public(evidence / "v0.20.0-runtime-issues-public.pem", issue_key)
    _write_json(ROOT / "fixtures/runtime/runtime-known-issues-v0.20.0.json", signed_issue_registry.model_dump(mode="json"))
    issue_context = RuntimeIssueContext(
        profile_id=runtime_manifest.profile_id, runtime_name=runtime_manifest.runtime_name,
        runtime_version=runtime_manifest.runtime_version, provider=runtime_manifest.execution_provider,
        compiler=f"python-{sys.version_info.major}.{sys.version_info.minor}", architecture=platform.machine(),
        graph_sha256=runtime_manifest.model_sha256, operators=("Linear", "Sigmoid"),
        attributes={"quantization": runtime_manifest.quantization},
    )
    issue_report = evaluate_runtime_known_issues(
        signed_issue_registry, issue_key.public_key(), issue_context, now=datetime(2026, 8, 3, 8, 6, tzinfo=timezone.utc)
    )
    issue_report["release_eligible"] = False
    issue_report["target_qualified"] = False
    issue_report_base = {key: value for key, value in issue_report.items() if key != "report_digest"}
    issue_report = {**issue_report_base, "report_digest": sha256_bytes(canonical_json_bytes(issue_report_base))}
    _write_json(ROOT / "runtime-known-issue-report.json", issue_report)

    # Release-model package and graph-capability admission. The fixture is intentionally
    # development-only and does not claim that ONNX Runtime is installed or target-qualified.
    release_model_root = ROOT / "artifacts/release-models/seismic-onnx-development"
    release_model_root.mkdir(parents=True, exist_ok=True)
    os.chmod(release_model_root, 0o755)
    onnx_model_path = release_model_root / "model.onnx"
    onnx_model_path.write_bytes(_development_onnx())
    os.chmod(onnx_model_path, 0o444)
    os.chmod(release_model_root, 0o555)
    input_contract = TensorAllocationContract(
        name="features", dtype="float32", rank=2,
        dimensions=(DimensionBound(minimum=1, maximum=8, symbol="N"), DimensionBound(minimum=3, maximum=3)),
        maximum_elements=24, maximum_bytes=96,
    )
    output_contract = TensorAllocationContract(
        name="score", dtype="float32", rank=2,
        dimensions=(DimensionBound(minimum=1, maximum=8, symbol="N"), DimensionBound(minimum=1, maximum=1)),
        maximum_elements=8, maximum_bytes=32,
    )
    model_package = ModelPackageManifest(
        package_id="seismic-onnx-development-v1", model_path="model.onnx", model_sha256=sha256_file(onnx_model_path),
        release_root="artifacts/release-models/seismic-onnx-development",
        package_files=(PackageFile(path="model.onnx", sha256=sha256_file(onnx_model_path), bytes=onnx_model_path.stat().st_size),),
        inputs=(input_contract,), outputs=(output_contract,), allowed_opsets={"ai.onnx": (18, 18)},
        allowed_operators={"ai.onnx": ("MatMul", "Sigmoid")}, expected_execution_provider="CPUExecutionProvider",
        created_at=datetime(2026, 8, 3, 8, 10, tzinfo=timezone.utc),
        expires_at=datetime(2026, 9, 2, 8, 10, tzinfo=timezone.utc),
    )
    model_package_path = ROOT / "fixtures/runtime/seismic-onnx-development.package.json"
    _write_json(model_package_path, model_package.model_dump(mode="json", by_alias=True))
    onnx_issue_context = RuntimeIssueContext(
        profile_id="seismic-onnx-development-v1", runtime_name="onnxruntime", runtime_version="development-contract",
        provider="CPUExecutionProvider", compiler=f"python-{sys.version_info.major}.{sys.version_info.minor}",
        architecture=platform.machine(), graph_sha256=model_package.model_sha256, operators=("MatMul", "Sigmoid"),
        attributes={"opset.ai.onnx": "18"},
    )
    onnx_issue_report = evaluate_runtime_known_issues(
        signed_issue_registry, issue_key.public_key(), onnx_issue_context, now=datetime(2026, 8, 3, 8, 11, tzinfo=timezone.utc)
    )
    _write_json(ROOT / "qualification/model-runtime-issue-evaluation.json", onnx_issue_report)
    runtime_context = RuntimeAdmissionContext(
        runtime_name="onnxruntime", runtime_version="development-contract", execution_provider="CPUExecutionProvider",
        compiler=f"python-{sys.version_info.major}.{sys.version_info.minor}", architecture=platform.machine(),
        runtime_package_sha256=sha256_file(lock_path), target_host_qualified=False, target_runtime_measured=False,
        provider_assignment_proven=True, fallback_observed=False,
    )
    _write_json(ROOT / "fixtures/runtime/seismic-onnx-development.runtime-context.json", runtime_context.model_dump(mode="json"))
    model_package_report = admit_model_package(
        model_package, root=ROOT, runtime=runtime_context, runtime_issue_evaluation=onnx_issue_report,
        now=datetime(2026, 8, 3, 8, 12, tzinfo=timezone.utc),
    )
    _write_json(ROOT / "qualification/model-package-admission.json", model_package_report)
    boundary_report = scan_model_execution_boundaries(ROOT)
    _write_json(ROOT / "qualification/model-execution-boundary-scan.json", boundary_report)

    # Signed signal-chain and commissioning evidence for the earthquake and wildfire hero fixtures.
    signal_key = Ed25519PrivateKey.generate()
    _write_public(evidence / "v0.20.0-signal-chain-public.pem", signal_key)
    imu_profile = SignalChainProfile(
        profile_id="earthquake-imu-chain-v1", hazard=HazardKind.EARTHQUAKE, sensor_kind=SensorKind.IMU,
        sensor_identity="imu-development-fixture", capture_interface="iio-char-device",
        driver_or_firmware_identity="development-driver-v1", adc_bits=16, sample_rate_hz=400.0, full_scale=16.0, unit="m/s2",
        anti_alias_filter=AntiAliasFilter(filter_id="fir-aa-v1", kind="FIR", cutoff_hz=40.0, order=64, evidence_sha256="b" * 64),
        rate_operations=(RateOperation(kind=RateOperationKind.DECIMATE, input_rate_hz=400.0, output_rate_hz=100.0, method="polyphase-fir", anti_alias_filter_required=True),),
        timestamp_source="kernel-monotonic-raw", maximum_timestamp_uncertainty_ms=0.5, maximum_fifo_delay_ms=5.0,
        maximum_rate_error_fraction=0.01, maximum_jitter_ms=0.5, maximum_gap_ms=15.0,
        axis_or_sector_identity="x-east/y-north/z-up", preprocessing_sha256="c" * 64,
        compatible_model_profile_ids=("seismic-trigger-v1", "seismic-onnx-development-v1"),
        created_at=datetime(2026, 8, 3, 8, 15, tzinfo=timezone.utc), expires_at=datetime(2026, 9, 2, 8, 15, tzinfo=timezone.utc),
    )
    signed_imu = sign_signal_chain_profile(imu_profile, signal_key, signed_at=datetime(2026, 8, 3, 8, 15, 1, tzinfo=timezone.utc))
    _write_json(ROOT / "fixtures/sensors/earthquake-imu-chain-v1.signed.json", signed_imu.model_dump(mode="json", by_alias=True))
    imu_observation = SignalChainObservation(
        source_class=SignalSourceClass.FIXTURE, sensor_kind=SensorKind.IMU, sensor_identity="imu-development-fixture",
        capture_interface="iio-char-device", driver_or_firmware_identity="development-driver-v1", adc_bits=16,
        observed_rate_hz=100.0, full_scale=16.0, unit="m/s2", anti_alias_filter_id="fir-aa-v1",
        rate_operations=imu_profile.rate_operations, timestamp_source="kernel-monotonic-raw", timestamp_uncertainty_ms=0.2,
        fifo_delay_ms=2.0, rate_error_fraction=0.002, p99_jitter_ms=0.2, maximum_gap_ms=11.0,
        clipping_samples=0, saturation_samples=0, quantization_minimum=-16.0, quantization_maximum=15.999,
        axis_or_sector_identity="x-east/y-north/z-up", preprocessing_sha256="c" * 64,
        commissioning_report_sha256=sha256_file(ROOT / "qualification/sensor-commissioning.json"),
        observed_at=datetime(2026, 8, 3, 8, 16, tzinfo=timezone.utc),
    )
    _write_json(ROOT / "fixtures/sensors/earthquake-imu-chain-v1.observation.json", imu_observation.model_dump(mode="json"))
    imu_signal_report = evaluate_signal_chain(
        signed_imu, signal_key.public_key(), imu_observation, model_profile_id="seismic-trigger-v1",
        now=datetime(2026, 8, 3, 8, 17, tzinfo=timezone.utc),
    )
    _write_json(ROOT / "qualification/signal-chain-evaluation.json", imu_signal_report)

    camera_profile = SignalChainProfile(
        profile_id="wildfire-camera-chain-v1", hazard=HazardKind.WILDFIRE, sensor_kind=SensorKind.CAMERA,
        sensor_identity="camera-development-fixture", capture_interface="v4l2-video-device",
        driver_or_firmware_identity="development-camera-driver-v1", sample_rate_hz=5.0, unit="rgb8-frame",
        rate_operations=(RateOperation(kind=RateOperationKind.NATIVE, input_rate_hz=5.0, output_rate_hz=5.0, method="native-capture"),),
        timestamp_source="camera-driver-monotonic", maximum_timestamp_uncertainty_ms=4.0, maximum_fifo_delay_ms=40.0,
        maximum_rate_error_fraction=0.05, maximum_jitter_ms=12.0, maximum_gap_ms=600.0,
        axis_or_sector_identity="sector-northwest/privacy-mask-v1", preprocessing_sha256="d" * 64,
        compatible_model_profile_ids=("wildfire-smoke-linear-v1",),
        created_at=datetime(2026, 8, 3, 8, 15, tzinfo=timezone.utc), expires_at=datetime(2026, 9, 2, 8, 15, tzinfo=timezone.utc),
    )
    signed_camera = sign_signal_chain_profile(camera_profile, signal_key, signed_at=datetime(2026, 8, 3, 8, 15, 2, tzinfo=timezone.utc))
    _write_json(ROOT / "fixtures/sensors/wildfire-camera-chain-v1.signed.json", signed_camera.model_dump(mode="json", by_alias=True))
    camera_observation = SignalChainObservation(
        source_class=SignalSourceClass.FIXTURE, sensor_kind=SensorKind.CAMERA, sensor_identity="camera-development-fixture",
        capture_interface="v4l2-video-device", driver_or_firmware_identity="development-camera-driver-v1",
        observed_rate_hz=5.0, unit="rgb8-frame", rate_operations=camera_profile.rate_operations,
        timestamp_source="camera-driver-monotonic", timestamp_uncertainty_ms=2.0, fifo_delay_ms=18.0,
        rate_error_fraction=0.01, p99_jitter_ms=5.0, maximum_gap_ms=250.0, clipping_samples=0, saturation_samples=0,
        quantization_minimum=0.0, quantization_maximum=255.0, axis_or_sector_identity="sector-northwest/privacy-mask-v1",
        preprocessing_sha256="d" * 64, commissioning_report_sha256=sha256_file(ROOT / "qualification/camera-commissioning.json"),
        observed_at=datetime(2026, 8, 3, 8, 16, tzinfo=timezone.utc),
    )
    _write_json(ROOT / "fixtures/sensors/wildfire-camera-chain-v1.observation.json", camera_observation.model_dump(mode="json"))
    camera_signal_report = evaluate_signal_chain(
        signed_camera, signal_key.public_key(), camera_observation, model_profile_id="wildfire-smoke-linear-v1",
        now=datetime(2026, 8, 3, 8, 17, tzinfo=timezone.utc),
    )
    _write_json(ROOT / "qualification/wildfire-signal-chain-evaluation.json", camera_signal_report)

    clipped_report = evaluate_signal_chain(
        signed_imu, signal_key.public_key(), imu_observation.model_copy(update={"clipping_samples": 3}),
        model_profile_id="seismic-trigger-v1", now=datetime(2026, 8, 3, 8, 17, tzinfo=timezone.utc),
    )
    saturated_report = evaluate_signal_chain(
        signed_imu, signal_key.public_key(), imu_observation.model_copy(update={"saturation_samples": 2}),
        model_profile_id="seismic-trigger-v1", now=datetime(2026, 8, 3, 8, 17, tzinfo=timezone.utc),
    )
    interpolation_profile = imu_profile.model_copy(update={
        "profile_id": "interpolated-signal-fixture-v1", "sample_rate_hz": 50.0, "anti_alias_filter": None,
        "rate_operations": (RateOperation(kind=RateOperationKind.INTERPOLATE, input_rate_hz=50.0, output_rate_hz=100.0, method="linear-interpolation"),),
    })
    signed_interpolation = sign_signal_chain_profile(interpolation_profile, signal_key, signed_at=datetime(2026, 8, 3, 8, 15, 3, tzinfo=timezone.utc))
    interpolation_observation = imu_observation.model_copy(update={
        "observed_rate_hz": 100.0, "anti_alias_filter_id": None, "rate_operations": interpolation_profile.rate_operations,
    })
    interpolation_report = evaluate_signal_chain(
        signed_interpolation, signal_key.public_key(), interpolation_observation, model_profile_id="seismic-trigger-v1",
        now=datetime(2026, 8, 3, 8, 17, tzinfo=timezone.utc),
    )
    conformance = {
        "schema": "sentinel-edge-signal-chain-conformance/1.0",
        "native": {"report_digest": camera_signal_report["report_digest"], "state": camera_signal_report["state"]},
        "decimated": {"report_digest": imu_signal_report["report_digest"], "state": imu_signal_report["state"]},
        "interpolated": {"report_digest": interpolation_report["report_digest"], "state": interpolation_report["state"]},
        "clipped": {"report_digest": clipped_report["report_digest"], "state": clipped_report["state"], "reasons": clipped_report["degraded_reason_codes"]},
        "saturated": {"report_digest": saturated_report["report_digest"], "state": saturated_report["state"], "reasons": saturated_report["degraded_reason_codes"]},
        "target_qualified": False,
    }
    conformance["report_digest"] = sha256_bytes(canonical_json_bytes(conformance))
    _write_json(ROOT / "qualification/signal-chain-conformance.json", conformance)

    commissioning_record = SiteCommissioningRecord(
        commissioning_id="earthquake-development-commissioning-v1", site_id="development-site",
        sensor_identity=imu_profile.sensor_identity, signal_chain_profile_sha256=signed_imu.profile_sha256,
        configuration_sha256=sha256_file(config_path), calibration_identity="development-calibration-v1",
        mounting_or_pose="fixture-level-north-aligned", datum_identity="local-building-frame-v1",
        baseline_noise_summary={"rms_m_s2": 0.02}, compatible_model_profile_ids=("seismic-trigger-v1",),
        actor="development-commissioner", created_at=datetime(2026, 8, 3, 8, 18, tzinfo=timezone.utc),
        expires_at=datetime(2026, 9, 2, 8, 18, tzinfo=timezone.utc),
    )
    signed_commissioning = sign_site_commissioning_record(commissioning_record, signal_key, signed_at=datetime(2026, 8, 3, 8, 18, 1, tzinfo=timezone.utc))
    _write_json(ROOT / "fixtures/sensors/earthquake-development-commissioning.signed.json", signed_commissioning.model_dump(mode="json", by_alias=True))
    commissioning_report = evaluate_site_commissioning(
        signed_commissioning, signal_key.public_key(), signal_chain_report=imu_signal_report,
        current_sensor_identity=imu_profile.sensor_identity, current_configuration_sha256=sha256_file(config_path),
        current_mounting_or_pose="fixture-level-north-aligned", current_model_profile_id="seismic-trigger-v1",
        now=datetime(2026, 8, 3, 8, 19, tzinfo=timezone.utc),
    )
    _write_json(ROOT / "qualification/site-commissioning.json", commissioning_report)

    repro_path = write_reproducibility_report(ROOT, ROOT / "reproducibility-report.json")
    host_path = write_host_trust_report(ROOT / "host-trust-report.json")
    write_cyclonedx_sbom(ROOT, ROOT / "sbom.cdx.json")
    write_third_party_inventory(ROOT, ROOT / "third-party-inventory.json")
    write_third_party_notices(ROOT, ROOT / "THIRD_PARTY_NOTICES.md")
    sbom = json.loads((ROOT / "sbom.cdx.json").read_text(encoding="utf-8"))
    snapshots = [
        ROOT / "fixtures/security/advisory-osv-bounded.json",
        ROOT / "fixtures/security/advisory-github_advisory-bounded.json",
        ROOT / "fixtures/security/advisory-cisa_kev-bounded.json",
        ROOT / "fixtures/security/advisory-vendor-bounded.json",
    ]
    review = build_security_review(sbom, [load_advisory_snapshot(path) for path in snapshots])
    review = apply_coverage_policy(review, AdvisoryCoveragePolicy(), toolchain_review=scan_toolchain_inventory([]))
    _write_json(ROOT / "security-review.json", review)

    repro = json.loads(repro_path.read_text(encoding="utf-8"))
    builder_a = Ed25519PrivateKey.generate(); builder_b = Ed25519PrivateKey.generate()
    host_fingerprint = sha256_bytes(canonical_json_bytes({"node": platform.node(), "machine": platform.machine(), "system": platform.system()}))
    attestations = [
        build_attestation(builder_id="sentinel-local-builder-a", host_fingerprint=host_fingerprint, environment_digest=sha256_bytes(b"v020-builder-a"), source_digest=repro["source_members_digest"], artifact_digest=repro["artifact_classes"][0]["build_a"]["sha256"], private_key=builder_a),
        build_attestation(builder_id="sentinel-local-builder-b", host_fingerprint=host_fingerprint, environment_digest=sha256_bytes(b"v020-builder-b"), source_digest=repro["source_members_digest"], artifact_digest=repro["artifact_classes"][0]["build_a"]["sha256"], private_key=builder_b),
    ]
    public_keys = {key_id(builder_a.public_key()): builder_a.public_key(), key_id(builder_b.public_key()): builder_b.public_key()}
    independent = build_independent_build_report(attestations, public_keys)
    write_independent_build_report(ROOT / "independent-build-report.json", independent)
    _write_public(evidence / "v0.20.0-builder-a-public.pem", builder_a)
    _write_public(evidence / "v0.20.0-builder-b-public.pem", builder_b)

    release_public = load_pem_public_key((evidence / "v0.20.0-release-public.pem").read_bytes())
    release_key_id = key_id(release_public)
    credential_profile = {
        "schema": "sentinel-edge-release-credential-profile/1.0",
        "private_key_storage": "external_offline_key",
        "development_bearer_tokens_present": False,
        "rotation_tested": True,
        "purpose_key_ids": {"release": release_key_id, "audit": "audit-key-v1", "update": "update-key-v1", "boot": "boot-key-unconfigured"},
        "evidence": ["tests/test_benchmark_governance_v018.py", "tests/test_release_closure_v017.py"],
    }
    governance = build_release_governance_report(
        packets=[], reviewer_public_keys={}, builder_ids={"sentinel-local-builder-a", "sentinel-local-builder-b"},
        release_signer_key_id=release_key_id, credential_profile=credential_profile,
    )
    write_release_governance_report(ROOT / "release-governance-report.json", governance)

    copies = {
        "requirements-release.lock.json": ROOT / "requirements-release.lock.json",
        "wheelhouse-report.json": ROOT / "wheelhouse-report.json",
        "target-wheelhouse-report.json": ROOT / "target-wheelhouse-report.json",
        "network-isolation-report.json": ROOT / "network-isolation-report.json",
        "isolated-benchmark-command.json": ROOT / "qualification/isolated-benchmark-command.json",
        "benchmark-identity-report.json": ROOT / "qualification/benchmark-identity-report.json",
        "benchmark-analysis-report.json": ROOT / "benchmark-analysis-report.json",
        "runtime-profile-qualification.json": ROOT / "qualification/runtime-profile-qualification.json",
        "reproducibility-report.json": ROOT / "reproducibility-report.json",
        "host-trust-report.json": ROOT / "host-trust-report.json",
        "sbom.cdx.json": ROOT / "sbom.cdx.json",
        "third-party-inventory.json": ROOT / "third-party-inventory.json",
        "third-party-notices.md": ROOT / "THIRD_PARTY_NOTICES.md",
        "security-review.json": ROOT / "security-review.json",
        "independent-build-report.json": ROOT / "independent-build-report.json",
        "release-governance-report.json": ROOT / "release-governance-report.json",
        "power-energy-report.json": ROOT / "power-energy-report.json",
        "runtime-known-issue-report.json": ROOT / "runtime-known-issue-report.json",
        "model-package-admission.json": ROOT / "qualification/model-package-admission.json",
        "model-execution-boundary-scan.json": ROOT / "qualification/model-execution-boundary-scan.json",
        "signal-chain-evaluation.json": ROOT / "qualification/signal-chain-evaluation.json",
        "wildfire-signal-chain-evaluation.json": ROOT / "qualification/wildfire-signal-chain-evaluation.json",
        "signal-chain-conformance.json": ROOT / "qualification/signal-chain-conformance.json",
        "site-commissioning.json": ROOT / "qualification/site-commissioning.json",
    }
    for name, source in copies.items():
        _copy_evidence(name, source)

    base = {
        "schema": "sentinel-edge-v020-evidence/1.0",
        "current_platform_wheelhouse": {"path": "wheelhouse-report.json", "sha256": sha256_file(ROOT / "wheelhouse-report.json"), "complete": current_wheel_report["complete"], "release_eligible": current_wheel_report["release_eligible"], "captured": capture["complete"]},
        "arm64_target_wheelhouse": {"path": "target-wheelhouse-report.json", "sha256": sha256_file(ROOT / "target-wheelhouse-report.json"), "complete": target_wheel_report["target_platform_complete"], "failures": target_wheel_report["failures"]},
        "isolated_benchmark_command": {"path": "qualification/isolated-benchmark-command.json", "sha256": sha256_file(ROOT / "qualification/isolated-benchmark-command.json"), "valid": isolated["valid"], "failures": isolated["failures"]},
        "benchmark_identity": {"path": "qualification/benchmark-identity-report.json", "sha256": sha256_file(ROOT / "qualification/benchmark-identity-report.json"), "measured_mode_allowed": identity_report["measured_mode_allowed"]},
        "benchmark_analysis": {"path": "benchmark-analysis-report.json", "sha256": sha256_file(ROOT / "benchmark-analysis-report.json"), "confirmatory": analysis["confirmatory"], "complete_pair_count": analysis["complete_pair_count"], "headline_eligible": analysis["headline_eligible"], "failures": analysis["failures"]},
        "power_energy": {"path": "power-energy-report.json", "sha256": sha256_file(ROOT / "power-energy-report.json"), "release_eligible": power_report["release_eligible"]},
        "runtime_known_issues": {"path": "runtime-known-issue-report.json", "sha256": sha256_file(ROOT / "runtime-known-issue-report.json"), "activation_allowed": issue_report["activation_allowed"], "release_eligible": issue_report["release_eligible"]},
        "model_package": {"path": "qualification/model-package-admission.json", "sha256": sha256_file(ROOT / "qualification/model-package-admission.json"), "admission_passed": model_package_report["admission_passed"], "target_qualified": model_package_report["target_qualified"], "release_admissible": model_package_report["release_admissible"], "failures": model_package_report["failures"], "limitations": model_package_report["limitations"]},
        "execution_boundary": {"path": "qualification/model-execution-boundary-scan.json", "sha256": sha256_file(ROOT / "qualification/model-execution-boundary-scan.json"), "valid": boundary_report["valid"], "findings": boundary_report["findings"]},
        "signal_chains": {"earthquake": {"path": "qualification/signal-chain-evaluation.json", "sha256": sha256_file(ROOT / "qualification/signal-chain-evaluation.json"), "state": imu_signal_report["state"], "verified_claim_allowed": imu_signal_report["verified_claim_allowed"]}, "wildfire": {"path": "qualification/wildfire-signal-chain-evaluation.json", "sha256": sha256_file(ROOT / "qualification/wildfire-signal-chain-evaluation.json"), "state": camera_signal_report["state"], "verified_claim_allowed": camera_signal_report["verified_claim_allowed"]}, "conformance_path": "qualification/signal-chain-conformance.json"},
        "site_commissioning": {"path": "qualification/site-commissioning.json", "sha256": sha256_file(ROOT / "qualification/site-commissioning.json"), "site_verified_claim_allowed": commissioning_report["site_verified_claim_allowed"], "review_or_degraded_only": commissioning_report["review_or_degraded_only"]},
        "contract_truth": {"implemented": 246, "confirmed": 497, "verified": 0, "h0_implemented": 93, "h0_open": 147},
        "limitations": [
            "The Arm64 target wheelhouse is intentionally incomplete; no publisher-origin target wheel is fabricated.",
            "The benchmark analysis is simulated and therefore cannot become a target measurement claim.",
            "Power, energy, memory-pressure and runtime-known-issue semantics are development-tested; Raspberry Pi target telemetry remains open.",
            "The ONNX package, signal-chain and commissioning receipts prove fail-closed development semantics only; the target runtime, provider assignment, physical signal and site qualification remain open.",
            "Independent builder and independent security/privacy/accessibility review gates remain open.",
        ],
    }
    receipt = {**base, "receipt_sha256": sha256_bytes(canonical_json_bytes(base))}
    _write_json(evidence / "v0.20.0-target-benchmark-governance.json", receipt)
    return receipt


if __name__ == "__main__":
    result = build()
    print(json.dumps(result, indent=2, sort_keys=True))
