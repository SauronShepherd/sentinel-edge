from __future__ import annotations

import json
import zipfile
import pytest
from typing import Any
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from sentinel_edge.benchmark import (
    BenchmarkAnalysisPlan,
    BenchmarkExecutionRecord,
    BenchmarkIdentitySet,
    BenchmarkSample,
    FileIdentitySpec,
    analyze_execution,
    sign_analysis_plan,
    verify_analysis_report,
    verify_file_identities,
    verify_signed_plan,
)
from sentinel_edge.domain.models import BenchmarkVariant, ClaimClass
from sentinel_edge.release.wheelhouse import verify_target_wheelhouse, verify_target_wheelhouse_report
from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file


def _reports(tmp_path: Path):
    network_base = {
        "schema": "sentinel-edge-network-isolation-report/1.0",
        "below_application_layer_proven": True,
        "valid": True,
        "release_eligible": True,
        "failures": [],
    }
    network = {**network_base, "report_digest": sha256_bytes(canonical_json_bytes(network_base))}
    host = {"schema": "host", "target_device_claim_allowed": True, "host_profile_match": True}
    runtime = ({"profile_id": "r1", "target_qualified": True},)
    wheel_base = {
        "schema": "sentinel-edge-target-wheelhouse-report/1.0",
        "target_platform_complete": True,
        "release_eligible": True,
        "failures": [],
    }
    wheel = {**wheel_base, "report_digest": sha256_bytes(canonical_json_bytes(wheel_base))}
    identities = BenchmarkIdentitySet(
        runtime_profile_sha256s=(sha256_bytes(canonical_json_bytes(runtime[0])),),
        model_sha256s=("a" * 64,),
        configuration_sha256="b" * 64,
        fixture_manifest_sha256="c" * 64,
        opportunity_manifest_sha256="d" * 64,
        host_report_sha256=sha256_bytes(canonical_json_bytes(host)),
        network_isolation_report_sha256=network["report_digest"],
        wheelhouse_report_sha256=wheel["report_digest"],
    )
    return network, host, runtime, wheel, identities


def _plan(identities: BenchmarkIdentitySet, claim_set: str = "confirmatory") -> BenchmarkAnalysisPlan:
    return BenchmarkAnalysisPlan(
        plan_id="plan-1",
        campaign_id="campaign-1",
        created_at=datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc),
        claim_set=claim_set,
        primary_metrics=("end_to_end_ms",),
        guardrails={"max_deadline_miss_rate": 0.01},
        exclusions=("thermal_invalid", "power_invalid"),
        confidence_level=0.95,
        bootstrap_resamples=200,
        variants=(BenchmarkVariant.B0, BenchmarkVariant.B1, BenchmarkVariant.O1),
        minimum_complete_pairs=2,
        stop_rule={"type": "fixed_complete_pairs", "count": 2},
        offered_load_manifest_sha256=identities.opportunity_manifest_sha256,
        identities=identities,
    )


def _execution(identities: BenchmarkIdentitySet, *, source=ClaimClass.MEASURED, target=True):
    samples = []
    values = {
        "p1": (100.0, 80.0, 70.0),
        "p2": (110.0, 90.0, 75.0),
    }
    index = 0
    for pair_id, triplet in values.items():
        for variant, value in zip(BenchmarkVariant, triplet):
            samples.append(BenchmarkSample(block_index=index, pair_id=pair_id, opportunity_key=pair_id, variant=variant, metrics={"end_to_end_ms": value}))
            index += 1
    return BenchmarkExecutionRecord(
        run_id="run-1",
        plan_sha256="placeholder",
        started_at=datetime(2026, 8, 3, 8, 5, tzinfo=timezone.utc),
        completed_at=datetime(2026, 8, 3, 8, 10, tzinfo=timezone.utc),
        source_class=source,
        identities=identities,
        observed_network_attempts=0,
        mutation_attempts=(),
        samples=tuple(samples),
        declared_target_run=target,
    )


def test_signed_plan_and_paired_report_can_be_headline_eligible(tmp_path: Path):
    network, host, runtime, wheel, identities = _reports(tmp_path)
    private = Ed25519PrivateKey.generate()
    signed = sign_analysis_plan(_plan(identities), private, signed_at=datetime(2026, 8, 3, 8, 1, tzinfo=timezone.utc))
    run = _execution(identities).model_copy(update={"plan_sha256": signed.plan_sha256})
    report = analyze_execution(signed, private.public_key(), run, network_report=network, host_report=host, runtime_qualifications=runtime, wheelhouse_report=wheel)
    assert report["headline_eligible"] is True
    assert report["complete_pair_count"] == 2
    assert report["metrics"]["end_to_end_ms"]["absolute"]["B0"]["mean"] == 105.0
    assert report["metrics"]["end_to_end_ms"]["paired_deltas"]["B1_minus_B0"]["sample_count"] == 2
    assert report["metrics"]["end_to_end_ms"]["paired_deltas"]["B1_minus_B0"]["percentage_delta"] == pytest.approx(-19.0476190476)
    assert report["targets"]["preclaimed_result_values"] is False
    assert report["results"]["source"] == "observed_execution_samples"
    output = tmp_path / "report.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    assert verify_analysis_report(output)["headline_eligible"] is True


def test_exploratory_report_is_never_headline_eligible(tmp_path: Path):
    network, host, runtime, wheel, identities = _reports(tmp_path)
    private = Ed25519PrivateKey.generate()
    signed = sign_analysis_plan(_plan(identities, "exploratory"), private, signed_at=datetime(2026, 8, 3, 8, 1, tzinfo=timezone.utc))
    run = _execution(identities).model_copy(update={"plan_sha256": signed.plan_sha256})
    report = analyze_execution(signed, private.public_key(), run, network_report=network, host_report=host, runtime_qualifications=runtime, wheelhouse_report=wheel)
    assert report["headline_eligible"] is False
    assert report["confirmatory"] is False


def test_network_attempt_and_mutation_invalidate_run(tmp_path: Path):
    network, host, runtime, wheel, identities = _reports(tmp_path)
    private = Ed25519PrivateKey.generate()
    signed = sign_analysis_plan(_plan(identities), private, signed_at=datetime(2026, 8, 3, 8, 1, tzinfo=timezone.utc))
    run = _execution(identities).model_copy(update={"plan_sha256": signed.plan_sha256, "observed_network_attempts": 1, "mutation_attempts": ("config",)})
    report = analyze_execution(signed, private.public_key(), run, network_report=network, host_report=host, runtime_qualifications=runtime, wheelhouse_report=wheel)
    assert "network_attempt_observed" in report["failures"]
    assert "benchmark_mutation_attempted" in report["failures"]
    assert report["headline_eligible"] is False


def test_excluded_run_records_remain_visible(tmp_path: Path):
    network, host, runtime, wheel, identities = _reports(tmp_path)
    private = Ed25519PrivateKey.generate()
    signed = sign_analysis_plan(_plan(identities), private, signed_at=datetime(2026, 8, 3, 8, 1, tzinfo=timezone.utc))
    run = _execution(identities)
    samples = list(run.samples)
    samples[-1] = samples[-1].model_copy(update={"excluded": True, "invalidation_reasons": ("thermal_invalid",)})
    run = run.model_copy(update={"plan_sha256": signed.plan_sha256, "samples": tuple(samples)})
    report = analyze_execution(signed, private.public_key(), run, network_report=network, host_report=host, runtime_qualifications=runtime, wheelhouse_report=wheel)
    assert report["invalidations"][0]["reason_codes"] == ["thermal_invalid"]
    assert report["attempted_candidates"][-1]["status"] == "invalid"
    assert report["attempted_candidates"][-1]["reason_codes"] == ["thermal_invalid"]
    assert "insufficient_complete_pairs" in report["failures"]


def test_signature_and_identity_mismatch_fail_closed(tmp_path: Path):
    _, _, _, _, identities = _reports(tmp_path)
    private = Ed25519PrivateKey.generate()
    signed = sign_analysis_plan(_plan(identities), private)
    assert verify_signed_plan(signed, Ed25519PrivateKey.generate().public_key())["valid"] is False
    artifact = tmp_path / "config.json"
    artifact.write_text("{}")
    report = verify_file_identities(tmp_path, (FileIdentitySpec(name="config", path="config.json", sha256="0" * 64),))
    assert report["measured_mode_allowed"] is False
    assert report["failures"] == ["identity_mismatch:config"]


def test_post_claim_tuning_changes_campaign_plan_digest(tmp_path: Path):
    _, _, _, _, identities = _reports(tmp_path)
    private = Ed25519PrivateKey.generate()
    signed = sign_analysis_plan(_plan(identities), private)
    tuned = signed.plan.model_copy(update={"campaign_id": "campaign-2", "guardrails": {"tuned": 1.0}})
    assert sign_analysis_plan(tuned, private).plan_sha256 != signed.plan_sha256


def _write_wheel(path: Path, name: str, version: str):
    dist = f"{name}-{version}.dist-info"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(f"{name}/__init__.py", "")
        zf.writestr(f"{dist}/METADATA", f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n")
        zf.writestr(f"{dist}/WHEEL", "Wheel-Version: 1.0\nTag: py3-none-any\n")
        zf.writestr(f"{dist}/RECORD", "")


def test_target_wheelhouse_requires_exact_local_publisher_evidence(tmp_path: Path):
    lock = {"resolved": [{"name": "demo", "version": "1.0", "state": "resolved"}]}
    lock_path = tmp_path / "lock.json"
    lock_path.write_text(json.dumps(lock))
    wheel = tmp_path / "demo-1.0-py3-none-any.whl"
    _write_wheel(wheel, "demo", "1.0")
    manifest = {
        "schema": "sentinel-edge-target-wheel-acquisition/1.0",
        "target_platform": "linux-aarch64",
        "entries": [{
            "name": "demo", "version": "1.0", "path": wheel.name,
            "sha256": sha256_file(wheel), "bytes": wheel.stat().st_size,
            "origin_kind": "publisher_index", "origin_url": "https://publisher.invalid/demo.whl",
            "publisher_origin_proven": True, "tags": ["py3-none-any"],
        }],
        "installation_rehearsal": {
            "success": True, "no_index": True, "require_hashes": True, "machine": "aarch64",
            "installed_lock_sha256": sha256_file(lock_path),
        },
    }
    manifest_path = tmp_path / "target.json"
    manifest_path.write_text(json.dumps(manifest))
    report = verify_target_wheelhouse(lock_path, manifest_path, root=tmp_path, required_target_tags=("py3-none-any", "cp313-cp313-manylinux_2_28_aarch64"))
    assert report["target_platform_complete"] is True
    output = tmp_path / "report.json"
    output.write_text(json.dumps(report))
    assert verify_target_wheelhouse_report(output)["release_eligible"] is True


def test_target_wheelhouse_does_not_accept_current_platform_substitution(tmp_path: Path):
    lock = {"resolved": [{"name": "demo", "version": "1.0", "state": "resolved"}]}
    lock_path = tmp_path / "lock.json"
    lock_path.write_text(json.dumps(lock))
    wheel = tmp_path / "demo-1.0-cp313-cp313-manylinux_2_28_x86_64.whl"
    _write_wheel(wheel, "demo", "1.0")
    manifest = {
        "schema": "sentinel-edge-target-wheel-acquisition/1.0",
        "target_platform": "linux-aarch64",
        "entries": [{
            "name": "demo", "version": "1.0", "path": wheel.name,
            "sha256": sha256_file(wheel), "bytes": wheel.stat().st_size,
            "origin_kind": "publisher_index", "origin_url": "https://publisher.invalid/demo.whl",
            "publisher_origin_proven": True, "tags": ["cp313-cp313-manylinux_2_28_x86_64"],
        }],
        "installation_rehearsal": {},
    }
    manifest_path = tmp_path / "target.json"
    manifest_path.write_text(json.dumps(manifest))
    report = verify_target_wheelhouse(lock_path, manifest_path, root=tmp_path, required_target_tags=("cp313-cp313-manylinux_2_28_aarch64",))
    assert report["target_platform_complete"] is False
    assert "target_locked_wheels_invalid" in report["failures"]


def test_isolated_benchmark_launcher_contract_with_mock():
    import subprocess
    from sentinel_edge.qualification.network_isolation import run_isolated_benchmark_command

    def runner(command: Any, **kwargs: Any) -> Any:
        payload = {
            "child_namespace": "net:[2]",
            "dns_probe_blocked": True,
            "tcp_probe_blocked": True,
            "misbehaving_adapter_blocked": True,
            "workload_started": True,
            "workload_returncode": 0,
            "workload_stdout": "ok",
            "workload_stderr": "",
        }
        return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")

    report = run_isolated_benchmark_command(["python", "-c", "print('ok')"], runner=runner)
    assert report["valid"] is True
    assert report["preflight_egress_blocked"] is True
