from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import ValidationError

from sentinel_edge.domain.models import HazardKind, SensorKind
from sentinel_edge.qualification import (
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
from sentinel_edge.runtime import (
    DimensionBound,
    ModelPackageManifest,
    PackageFile,
    ProtobufParseError,
    RuntimeAdmissionContext,
    TensorAllocationContract,
    admit_model_package,
    inspect_onnx_graph_bounded,
    onnx_worker_policy,
    inspect_onnx_graph,
    scan_model_execution_boundaries,
)
from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file

NOW = datetime(2026, 8, 3, 9, 30, tzinfo=timezone.utc)


def _varint(value: int) -> bytes:
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def _field_varint(number: int, value: int) -> bytes:
    return _varint((number << 3) | 0) + _varint(value)


def _field_bytes(number: int, value: bytes) -> bytes:
    return _varint((number << 3) | 2) + _varint(len(value)) + value


def _field_text(number: int, value: str) -> bytes:
    return _field_bytes(number, value.encode())


def _dimension(value: int | str | None) -> bytes:
    if isinstance(value, int):
        return _field_varint(1, value)
    if isinstance(value, str):
        return _field_text(2, value)
    return b""


def _value_info(name: str, dtype: int, dims: tuple[int | str | None, ...]) -> bytes:
    shape = b"".join(_field_bytes(1, _dimension(item)) for item in dims)
    tensor_type = _field_varint(1, dtype) + _field_bytes(2, shape)
    type_proto = _field_bytes(1, tensor_type)
    return _field_text(1, name) + _field_bytes(2, type_proto)


def _node(op_type: str, *, domain: str = "", attribute_name: str | None = None, subgraph: bytes | None = None) -> bytes:
    payload = _field_text(4, op_type)
    if domain:
        payload += _field_text(7, domain)
    if attribute_name is not None:
        attr = _field_text(1, attribute_name)
        if subgraph is not None:
            attr += _field_bytes(6, subgraph) + _field_varint(20, 5)
        else:
            attr += _field_varint(3, 1) + _field_varint(20, 2)
        payload += _field_bytes(5, attr)
    return payload


def _tensor(name: str, dims: tuple[int, ...], *, external_location: str | None = None) -> bytes:
    payload = b"".join(_field_varint(1, item) for item in dims)
    payload += _field_varint(2, 1) + _field_text(8, name)
    if external_location is None:
        payload += _field_bytes(9, b"\x00" * (4 * max(1, dims[0] * dims[-1])))
    else:
        entry = _field_text(1, "location") + _field_text(2, external_location)
        payload += _field_bytes(13, entry) + _field_varint(14, 1)
    return payload


def _onnx_model(*, input_dims=("N", 3), external_location: str | None = None, control_flow: bool = False) -> bytes:
    nodes = [_node("MatMul"), _node("Sigmoid", attribute_name="fixture")]
    if control_flow:
        nested_graph = _field_bytes(1, _node("Identity"))
        nodes.append(_node("If", attribute_name="then_branch", subgraph=nested_graph))
    graph = b"".join(_field_bytes(1, item) for item in nodes)
    graph += _field_bytes(5, _tensor("weight", (3, 1), external_location=external_location))
    graph += _field_bytes(11, _value_info("features", 1, tuple(input_dims)))
    graph += _field_bytes(12, _value_info("score", 1, (input_dims[0], 1)))
    opset = _field_text(1, "") + _field_varint(2, 18)
    return _field_varint(1, 9) + _field_bytes(7, graph) + _field_bytes(8, opset)


def _contracts() -> tuple[tuple[TensorAllocationContract, ...], tuple[TensorAllocationContract, ...]]:
    inputs = (
        TensorAllocationContract(
            name="features",
            dtype="float32",
            rank=2,
            dimensions=(DimensionBound(minimum=1, maximum=8, symbol="N"), DimensionBound(minimum=3, maximum=3)),
            maximum_elements=24,
            maximum_bytes=96,
        ),
    )
    outputs = (
        TensorAllocationContract(
            name="score",
            dtype="float32",
            rank=2,
            dimensions=(DimensionBound(minimum=1, maximum=8, symbol="N"), DimensionBound(minimum=1, maximum=1)),
            maximum_elements=8,
            maximum_bytes=32,
        ),
    )
    return inputs, outputs


def _package(tmp_path: Path, model: bytes, **changes) -> tuple[Path, ModelPackageManifest]:
    release = tmp_path / "artifacts" / "release-models" / "fixture"
    release.mkdir(parents=True)
    model_path = release / "model.onnx"
    model_path.write_bytes(model)
    model_path.chmod(0o444)
    release.chmod(0o555)
    inputs, outputs = _contracts()
    payload = {
        "package_id": "fixture-onnx-v1",
        "model_path": "model.onnx",
        "model_sha256": sha256_file(model_path),
        "release_root": "artifacts/release-models/fixture",
        "package_files": (PackageFile(path="model.onnx", sha256=sha256_file(model_path), bytes=model_path.stat().st_size),),
        "inputs": inputs,
        "outputs": outputs,
        "allowed_opsets": {"ai.onnx": (18, 18)},
        "allowed_operators": {"ai.onnx": ("MatMul", "Sigmoid")},
        "expected_execution_provider": "CPUExecutionProvider",
        "created_at": NOW,
        "expires_at": NOW + timedelta(days=30),
    }
    payload.update(changes)
    return model_path, ModelPackageManifest(**payload)


def _runtime(**changes) -> RuntimeAdmissionContext:
    payload = {
        "runtime_name": "onnxruntime",
        "runtime_version": "1.23.0",
        "execution_provider": "CPUExecutionProvider",
        "compiler": "gcc-14",
        "architecture": "x86_64",
        "runtime_package_sha256": "a" * 64,
        "provider_assignment_proven": True,
    }
    payload.update(changes)
    return RuntimeAdmissionContext(**payload)


def test_onnx_fingerprint_includes_opsets_operators_shapes_and_initializers(tmp_path: Path) -> None:
    path = tmp_path / "model.onnx"
    path.write_bytes(_onnx_model())
    report = inspect_onnx_graph(path)
    assert report["ir_version"] == 9
    assert report["opsets"] == [{"domain": "ai.onnx", "version": 18}]
    assert [item["operator"] for item in report["operators"]] == ["MatMul", "Sigmoid"]
    assert report["inputs"][0]["dimensions"] == ["N", 3]
    assert report["initializers"][0]["name"] == "weight"
    assert len(report["graph_capability_sha256"]) == 64


def test_onnx_inspection_worker_is_bounded_and_deterministic(tmp_path: Path) -> None:
    path = tmp_path / "model.onnx"
    path.write_bytes(_onnx_model())
    first = inspect_onnx_graph_bounded(path)
    second = inspect_onnx_graph_bounded(path)
    assert first["graph_capability_sha256"] == second["graph_capability_sha256"]


def test_onnx_inspection_worker_rejects_invalid_budget(tmp_path: Path) -> None:
    path = tmp_path / "model.onnx"
    path.write_bytes(_onnx_model())
    with pytest.raises(ValueError, match="timeout_seconds"):
        inspect_onnx_graph_bounded(path, timeout_seconds=0)


def test_onnx_worker_policy_discloses_target_qualification_limits() -> None:
    policy = onnx_worker_policy()
    assert policy["timeout_seconds"] == 5.0
    assert policy["cpu_seconds"] == 6
    assert policy["address_space_bytes"] == 512 * 1024 * 1024
    assert policy["file_descriptors"] == 64
    assert policy["close_fds"] is True


def test_manifest_bounded_symbolic_shape_admits_development_package(tmp_path: Path) -> None:
    _, package = _package(tmp_path, _onnx_model())
    report = admit_model_package(
        package,
        root=tmp_path,
        runtime=_runtime(),
        runtime_issue_evaluation={"activation_allowed": True, "target_qualified": False},
        now=NOW + timedelta(minutes=1),
    )
    assert report["admission_passed"] is True
    assert report["input_allocation_bytes"] == 96
    assert report["output_allocation_bytes"] == 32
    assert report["target_qualified"] is False
    assert report["runtime_name"] == "onnxruntime"
    assert report["runtime_version"] == "1.23.0"
    assert report["runtime_package_sha256"] == "a" * 64
    assert report["execution_provider"] == "CPUExecutionProvider"
    assert set(report["limitations"]) == {"target_host_not_qualified", "target_runtime_not_measured"}
    assert [item["provider"] for item in report["provider_assignment"]] == [
        "CPUExecutionProvider", "CPUExecutionProvider"
    ]


def test_unknown_dynamic_dimension_and_control_flow_fail_before_execution(tmp_path: Path) -> None:
    _, package = _package(tmp_path, _onnx_model(input_dims=(None, 3), control_flow=True))
    report = admit_model_package(
        package,
        root=tmp_path,
        runtime=_runtime(),
        runtime_issue_evaluation={"activation_allowed": True},
        now=NOW + timedelta(minutes=1),
    )
    assert "input_unknown_dimension:features:0" in report["failures"]
    assert any(item.startswith("control_flow_not_allowed") for item in report["failures"])


@pytest.mark.parametrize("field", ["python_ops_allowed", "custom_op_libraries", "runtime_extensions", "plugin_execution_providers"])
def test_capability_injection_is_rejected_at_manifest_admission(tmp_path: Path, field: str) -> None:
    value = True if field == "python_ops_allowed" else ("untrusted-extension",)
    with pytest.raises(ValueError, match="(Python operators|executable extensions)"):
        _package(tmp_path, _onnx_model(), **{field: value})


def test_external_data_escape_and_unapproved_custom_operator_fail_closed(tmp_path: Path) -> None:
    model = _onnx_model(external_location="../weights.bin")
    _, package = _package(
        tmp_path,
        model,
        external_data_allowed=True,
        allowed_operators={"ai.onnx": ("MatMul", "Sigmoid")},
    )
    report = admit_model_package(
        package,
        root=tmp_path,
        runtime=_runtime(),
        runtime_issue_evaluation={"activation_allowed": True},
        now=NOW + timedelta(minutes=1),
    )
    assert "external_data_path_unsafe:../weights.bin" in report["failures"]
    assert "external_data_not_manifest_approved:../weights.bin" in report["failures"]


def test_malformed_onnx_attack_corpus_is_bounded(tmp_path: Path) -> None:
    corpus = [b"\x80", b"\x3a\x05abc", b"\x00", b"\xff" * 128]
    for index, payload in enumerate(corpus):
        path = tmp_path / f"bad-{index}.onnx"
        path.write_bytes(payload)
        with pytest.raises(ProtobufParseError):
            inspect_onnx_graph(path)


def test_model_execution_boundary_scan_detects_release_package_import(tmp_path: Path) -> None:
    package = tmp_path / "src" / "sentinel_edge" / "gateway"
    package.mkdir(parents=True)
    (package / "bad.py").write_text("import onnxruntime\n", encoding="utf-8")
    report = scan_model_execution_boundaries(tmp_path)
    assert report["valid"] is False
    assert report["findings"][0]["kind"] == "runtime_import_outside_component_3"


def _signal_profile() -> SignalChainProfile:
    return SignalChainProfile(
        profile_id="imu-seismic-v1",
        hazard=HazardKind.EARTHQUAKE,
        sensor_kind=SensorKind.IMU,
        sensor_identity="imu-fixture-001",
        capture_interface="iio-char-device",
        driver_or_firmware_identity="fixture-driver-v1",
        adc_bits=16,
        sample_rate_hz=400.0,
        full_scale=16.0,
        unit="m/s2",
        anti_alias_filter=AntiAliasFilter(filter_id="fir-aa-v1", kind="FIR", cutoff_hz=40.0, order=64, evidence_sha256="b" * 64),
        rate_operations=(
            RateOperation(kind=RateOperationKind.DECIMATE, input_rate_hz=400.0, output_rate_hz=100.0, method="polyphase-fir", anti_alias_filter_required=True),
        ),
        timestamp_source="kernel-monotonic-raw",
        maximum_timestamp_uncertainty_ms=0.5,
        maximum_fifo_delay_ms=5.0,
        maximum_rate_error_fraction=0.01,
        maximum_jitter_ms=0.5,
        maximum_gap_ms=15.0,
        axis_or_sector_identity="x-east/y-north/z-up",
        preprocessing_sha256="c" * 64,
        compatible_model_profile_ids=("seismic-trigger-v1",),
        created_at=NOW,
        expires_at=NOW + timedelta(days=30),
    )


def _observation(**changes) -> SignalChainObservation:
    payload = {
        "source_class": SignalSourceClass.FIXTURE,
        "sensor_kind": SensorKind.IMU,
        "sensor_identity": "imu-fixture-001",
        "capture_interface": "iio-char-device",
        "driver_or_firmware_identity": "fixture-driver-v1",
        "adc_bits": 16,
        "observed_rate_hz": 100.0,
        "full_scale": 16.0,
        "unit": "m/s2",
        "anti_alias_filter_id": "fir-aa-v1",
        "rate_operations": _signal_profile().rate_operations,
        "timestamp_source": "kernel-monotonic-raw",
        "timestamp_uncertainty_ms": 0.2,
        "fifo_delay_ms": 2.0,
        "rate_error_fraction": 0.002,
        "p99_jitter_ms": 0.2,
        "maximum_gap_ms": 11.0,
        "clipping_samples": 0,
        "saturation_samples": 0,
        "quantization_minimum": -16.0,
        "quantization_maximum": 15.999,
        "axis_or_sector_identity": "x-east/y-north/z-up",
        "preprocessing_sha256": "c" * 64,
        "commissioning_report_sha256": "d" * 64,
        "observed_at": NOW + timedelta(minutes=2),
    }
    payload.update(changes)
    return SignalChainObservation(**payload)


def test_signed_signal_chain_fixture_is_compatible_but_not_physical_claim() -> None:
    key = Ed25519PrivateKey.generate()
    signed = sign_signal_chain_profile(_signal_profile(), key, signed_at=NOW + timedelta(seconds=1))
    report = evaluate_signal_chain(signed, key.public_key(), _observation(), model_profile_id="seismic-trigger-v1", now=NOW + timedelta(minutes=3))
    assert report["compatibility_passed"] is True
    assert report["quality_passed"] is True
    assert report["state"] == "tested"
    assert report["verified_claim_allowed"] is False


def test_signal_saturation_and_timing_faults_degrade_and_invalidate_evidence() -> None:
    key = Ed25519PrivateKey.generate()
    signed = sign_signal_chain_profile(_signal_profile(), key, signed_at=NOW + timedelta(seconds=1))
    report = evaluate_signal_chain(
        signed,
        key.public_key(),
        _observation(saturation_samples=4, clipping_samples=2, p99_jitter_ms=1.2, fifo_delay_ms=8.0),
        model_profile_id="seismic-trigger-v1",
        now=NOW + timedelta(minutes=3),
    )
    assert report["state"] == "blocked"
    assert report["latency_quality_evidence_valid"] is False
    assert {"saturation_detected", "clipping_detected", "sample_jitter_out_of_envelope", "fifo_delay_out_of_envelope"} <= set(report["degraded_reason_codes"])


def test_signal_profile_rejects_decimation_without_antialias_evidence() -> None:
    payload = _signal_profile().model_dump(mode="python", by_alias=True)
    payload["anti_alias_filter"] = None
    with pytest.raises(ValidationError):
        SignalChainProfile.model_validate(payload)


def test_signal_chain_material_change_forces_failure() -> None:
    key = Ed25519PrivateKey.generate()
    signed = sign_signal_chain_profile(_signal_profile(), key, signed_at=NOW + timedelta(seconds=1))
    report = evaluate_signal_chain(
        signed,
        key.public_key(),
        _observation(sensor_identity="replacement-imu", preprocessing_sha256="e" * 64),
        model_profile_id="different-model",
        now=NOW + timedelta(minutes=3),
    )
    assert report["state"] == "failed"
    assert "signal_chain_mismatch:sensor_identity" in report["failures"]
    assert "signal_chain_mismatch:preprocessing_sha256" in report["failures"]
    assert "model_profile_not_signal_compatible" in report["failures"]


def test_signed_commissioning_record_is_review_only_for_fixture_and_physical_when_complete() -> None:
    key = Ed25519PrivateKey.generate()
    signed_profile = sign_signal_chain_profile(_signal_profile(), key, signed_at=NOW + timedelta(seconds=1))
    fixture_signal = evaluate_signal_chain(signed_profile, key.public_key(), _observation(), model_profile_id="seismic-trigger-v1", now=NOW + timedelta(minutes=3))
    record = SiteCommissioningRecord(
        commissioning_id="commissioning-001",
        site_id="site-fixture",
        sensor_identity="imu-fixture-001",
        signal_chain_profile_sha256=signed_profile.profile_sha256,
        configuration_sha256="f" * 64,
        calibration_identity="calibration-v1",
        mounting_or_pose="bolted-level-north-aligned",
        datum_identity="local-building-frame-v1",
        baseline_noise_summary={"rms_m_s2": 0.02},
        compatible_model_profile_ids=("seismic-trigger-v1",),
        actor="commissioning-admin",
        created_at=NOW,
        expires_at=NOW + timedelta(days=30),
    )
    signed_record = sign_site_commissioning_record(record, key, signed_at=NOW + timedelta(seconds=2))
    fixture_report = evaluate_site_commissioning(
        signed_record,
        key.public_key(),
        signal_chain_report=fixture_signal,
        current_sensor_identity="imu-fixture-001",
        current_configuration_sha256="f" * 64,
        current_mounting_or_pose="bolted-level-north-aligned",
        current_model_profile_id="seismic-trigger-v1",
        now=NOW + timedelta(minutes=4),
    )
    assert fixture_report["review_or_degraded_only"] is True
    physical_signal = {**fixture_signal, "physical_source_proven": True, "quality_passed": True}
    physical_report = evaluate_site_commissioning(
        signed_record,
        key.public_key(),
        signal_chain_report=physical_signal,
        current_sensor_identity="imu-fixture-001",
        current_configuration_sha256="f" * 64,
        current_mounting_or_pose="bolted-level-north-aligned",
        current_model_profile_id="seismic-trigger-v1",
        now=NOW + timedelta(minutes=4),
    )
    assert physical_report["site_verified_claim_allowed"] is True


def test_replacement_or_remount_invalidates_current_commissioning_without_rewriting_identity() -> None:
    key = Ed25519PrivateKey.generate()
    signed_profile = sign_signal_chain_profile(_signal_profile(), key, signed_at=NOW + timedelta(seconds=1))
    signal = evaluate_signal_chain(signed_profile, key.public_key(), _observation(source_class="physical"), model_profile_id="seismic-trigger-v1", now=NOW + timedelta(minutes=3))
    record = SiteCommissioningRecord(
        commissioning_id="commissioning-history-001",
        site_id="site-1",
        sensor_identity="imu-fixture-001",
        signal_chain_profile_sha256=signed_profile.profile_sha256,
        configuration_sha256="f" * 64,
        calibration_identity="calibration-v1",
        mounting_or_pose="mount-v1",
        baseline_noise_summary={"rms_m_s2": 0.02},
        compatible_model_profile_ids=("seismic-trigger-v1",),
        actor="commissioning-admin",
        created_at=NOW,
        expires_at=NOW + timedelta(days=30),
    )
    signed_record = sign_site_commissioning_record(record, key, signed_at=NOW + timedelta(seconds=2))
    report = evaluate_site_commissioning(
        signed_record,
        key.public_key(),
        signal_chain_report=signal,
        current_sensor_identity="imu-replacement",
        current_configuration_sha256="f" * 64,
        current_mounting_or_pose="mount-v2",
        current_model_profile_id="seismic-trigger-v1",
        now=NOW + timedelta(minutes=4),
    )
    assert report["site_verified_claim_allowed"] is False
    assert {"commissioning_sensor_replaced", "commissioning_mounting_changed"} <= set(report["failures"])
    assert report["commissioning_id"] == "commissioning-history-001"
    assert report["calibration_identity"] == "calibration-v1"
