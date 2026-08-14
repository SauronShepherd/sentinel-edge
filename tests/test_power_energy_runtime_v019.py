from __future__ import annotations

from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from sentinel_edge.benchmark import (
    BenchmarkAnalysisPlan,
    BenchmarkExecutionRecord,
    BenchmarkIdentitySet,
    BenchmarkSample,
    analyze_execution,
    sign_analysis_plan,
)
from sentinel_edge.domain.models import BenchmarkVariant, ClaimClass
from sentinel_edge.gateway import create_app
from sentinel_edge.qualification import (
    EnergyEvidenceKind,
    EnergyMeasurement,
    PowerHealthMonitor,
    PowerServiceState,
    PowerTelemetrySample,
    evaluate_energy_comparison,
    disclose_external_energy_method,
    observe_benchmark_host,
)
from sentinel_edge.scenario import DeterministicScenarioEngine
from sentinel_edge.security import canonical_json_bytes, sha256_bytes

NOW = datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc)


def _sample(**changes) -> PowerTelemetrySample:
    payload = {
        "observed_at": NOW,
        "temperature_c": 52.0,
        "source": "development-fixture",
    }
    payload.update(changes)
    return PowerTelemetrySample(**payload)


def _energy(*, quality: bool = True, kind: EnergyEvidenceKind = EnergyEvidenceKind.PHYSICAL, target: str = "quality-v1") -> EnergyMeasurement:
    common = {
        "kind": kind,
        "source_class": "measured",
        "scenario_window_id": "window-1",
        "method": "external-inline-meter" if kind is EnergyEvidenceKind.PHYSICAL else "cpu-time-proxy",
        "quality_target_id": target,
        "quality_guardrail_passed": quality,
        "complete_node_scope": kind is EnergyEvidenceKind.PHYSICAL,
        "included_components": ("node", "storage", "cooling") if kind is EnergyEvidenceKind.PHYSICAL else (),
    }
    if kind is EnergyEvidenceKind.PHYSICAL:
        return EnergyMeasurement(**common, energy_j=4.2, sampling_hz=10.0, idle_energy_j=0.5, uncertainty_j=0.1, instrument_id="fixture-meter", meter_coverage_fraction=1.0, meter_alignment_ms=10.0)
    return EnergyMeasurement(**common, proxy_value=12.0, proxy_unit="cpu_seconds")


def test_power_state_separates_current_history_and_requires_recovery_hysteresis() -> None:
    monitor = PowerHealthMonitor(required_recovery_samples=2)
    degraded = monitor.observe(_sample(under_voltage_current=True, under_voltage_history=True))
    assert degraded.state is PowerServiceState.DEGRADED_POWER
    assert degraded.current_power_threat is True
    recovering = monitor.observe(_sample(under_voltage_history=True))
    assert recovering.state is PowerServiceState.RECOVERING
    healthy = monitor.observe(_sample(under_voltage_history=True))
    assert healthy.state is PowerServiceState.HEALTHY
    assert healthy.current_power_threat is False
    assert healthy.historical_power_event_seen is True


def test_energy_evidence_never_labels_proxy_as_physical_and_fixes_quality_target() -> None:
    proxy = evaluate_energy_comparison((_energy(kind=EnergyEvidenceKind.PROXY),) * 3)
    assert proxy["proxy_only"] is True
    assert proxy["physical_energy_reportable"] is False
    physical = evaluate_energy_comparison((_energy(), _energy(), _energy()))
    assert physical["physical_energy_reportable"] is True
    mismatch = evaluate_energy_comparison((_energy(target="a"), _energy(target="b")))
    assert "quality_target_changed_between_variants" in mismatch["failures"]
    failed_quality = evaluate_energy_comparison((_energy(quality=False),))
    assert "quality_guardrail_failed" in failed_quality["failures"]


def test_energy_claim_fails_closed_for_meter_dropout_and_misalignment() -> None:
    dropout = _energy().model_copy(update={"meter_coverage_fraction": 0.75})
    misaligned = _energy().model_copy(update={"meter_alignment_ms": 1500.0})
    assert "meter_coverage_insufficient" in evaluate_energy_comparison((dropout,))["failures"]
    assert "meter_alignment_insufficient" in evaluate_energy_comparison((misaligned,))["failures"]
    assert evaluate_energy_comparison((dropout,))["physical_energy_reportable"] is False
    assert evaluate_energy_comparison((misaligned,))["physical_energy_reportable"] is False
    assert evaluate_energy_comparison((dropout,))["headline_energy_j"] is None
    assert evaluate_energy_comparison((misaligned,))["headline_energy_j"] is None


def test_external_energy_method_disclosure_is_complete_and_rejects_proxy() -> None:
    disclosure = disclose_external_energy_method(_energy())
    assert {"method", "instrument_id", "sampling_hz", "uncertainty_j", "meter_coverage_fraction", "meter_alignment_ms"} <= disclosure.keys()
    import pytest
    with pytest.raises(ValueError, match="physical measurement"):
        disclose_external_energy_method(_energy(kind=EnergyEvidenceKind.PROXY))


def test_benchmark_analysis_retains_power_and_memory_invalidations() -> None:
    host = {"target_device_claim_allowed": True, "host": "target-fixture"}
    network_base = {"schema": "sentinel-edge-network-isolation-report/1.0", "below_application_layer_proven": True, "release_eligible": True, "failures": []}
    network = {**network_base, "report_digest": sha256_bytes(canonical_json_bytes(network_base))}
    runtime = ({"target_qualified": True, "profile": "fixture"},)
    wheel = {"target_platform_complete": True, "report_digest": "8" * 64}
    identities = BenchmarkIdentitySet(
        runtime_profile_sha256s=tuple(sha256_bytes(canonical_json_bytes(item)) for item in runtime),
        model_sha256s=("1" * 64,),
        configuration_sha256="2" * 64,
        fixture_manifest_sha256="3" * 64,
        opportunity_manifest_sha256="4" * 64,
        host_report_sha256=sha256_bytes(canonical_json_bytes(host)),
        network_isolation_report_sha256=network["report_digest"],
        wheelhouse_report_sha256=wheel["report_digest"],
    )
    plan = BenchmarkAnalysisPlan(
        plan_id="power-memory-plan",
        campaign_id="power-memory-campaign",
        created_at=NOW,
        claim_set="confirmatory",
        primary_metrics=("end_to_end_ms", "energy_j"),
        guardrails={"physical_energy_required": 1.0, "max_memory_psi_avg10": 0.5, "max_major_faults_delta": 0},
        exclusions=("under_voltage_current", "frequency_capped_current", "swap_in_use"),
        confidence_level=0.95,
        bootstrap_resamples=100,
        variants=tuple(BenchmarkVariant),
        minimum_complete_pairs=2,
        stop_rule={"type": "fixed_complete_pairs", "count": 2},
        offered_load_manifest_sha256=identities.opportunity_manifest_sha256,
        identities=identities,
    )
    key = Ed25519PrivateKey.generate()
    signed = sign_analysis_plan(plan, key, signed_at=NOW + timedelta(seconds=1))
    samples = []
    block = 0
    for pair in ("p1", "p2"):
        for variant in BenchmarkVariant:
            platform = _sample(observed_at=NOW + timedelta(seconds=block))
            if pair == "p2" and variant is BenchmarkVariant.B1:
                platform = _sample(
                    observed_at=NOW + timedelta(seconds=block),
                    frequency_capped_current=True,
                    frequency_capped_history=True,
                    swap_total_mb=128,
                    swap_used_mb=16,
                    major_faults_delta=2,
                    memory_psi_avg10=1.2,
                )
            samples.append(BenchmarkSample(
                block_index=block,
                pair_id=pair,
                opportunity_key=pair,
                variant=variant,
                metrics={"end_to_end_ms": 10.0 + block, "energy_j": 4.2},
                platform=platform,
                energy=_energy(),
            ))
            block += 1
    run = BenchmarkExecutionRecord(
        run_id="fixture-run",
        plan_sha256=signed.plan_sha256,
        started_at=NOW + timedelta(seconds=2),
        completed_at=NOW + timedelta(seconds=20),
        source_class=ClaimClass.MEASURED,
        identities=identities,
        observed_network_attempts=0,
        samples=tuple(samples),
        declared_target_run=True,
    )
    report = analyze_execution(signed, key.public_key(), run, network_report=network, host_report=host, runtime_qualifications=runtime, wheelhouse_report=wheel)
    reasons = set(report["invalidations"][0]["reason_codes"])
    assert {"frequency_capped_current", "swap_in_use", "major_faults_above_envelope", "memory_pressure_above_envelope"} <= reasons
    assert report["platform_health"]["current_frequency_cap_count"] == 1
    assert "insufficient_complete_pairs" in report["failures"]


def test_power_health_api_exposes_current_and_history(operator_headers: dict[str, str]) -> None:
    client = TestClient(create_app(DeterministicScenarioEngine()))
    payload = _sample(under_voltage_current=True, under_voltage_history=True).model_dump(mode="json")
    response = client.post("/v1/platform/power/evaluate", json=payload, headers=operator_headers)
    assert response.status_code == 200
    assert response.json()["snapshot"]["state"] == "degraded_power"
    observed = client.get("/v1/platform/power", headers=operator_headers)
    assert observed.status_code == 200
    assert observed.json()["snapshot"]["current_power_threat"] is True
    assert len(observed.json()["history"]) == 1


def test_benchmark_host_observation_exposes_memory_pressure_and_swap_facts() -> None:
    report = observe_benchmark_host(provider_threads=1)
    assert "major_faults_total" in report
    assert "memory_pressure" in report
    assert "zram_devices" in report
    assert "SwapTotal" in report["page_cache"]


def test_schema_aliases_serialize_without_shadow_fields() -> None:
    identities = BenchmarkIdentitySet(
        runtime_profile_sha256s=("1" * 64,), model_sha256s=("2" * 64,), configuration_sha256="3" * 64,
        fixture_manifest_sha256="4" * 64, opportunity_manifest_sha256="5" * 64, host_report_sha256="6" * 64,
        network_isolation_report_sha256="7" * 64, wheelhouse_report_sha256="8" * 64,
    )
    plan = BenchmarkAnalysisPlan(
        plan_id="schema", created_at=NOW, claim_set="exploratory", primary_metrics=("latency",), guardrails={}, exclusions=(),
        campaign_id="schema-campaign",
        confidence_level=.95, bootstrap_resamples=100, variants=tuple(BenchmarkVariant), minimum_complete_pairs=2,
        stop_rule={"type": "fixed"}, offered_load_manifest_sha256="5" * 64, identities=identities,
    )
    dumped = plan.model_dump(mode="json")
    assert dumped["schema"] == "sentinel-edge-benchmark-analysis-plan/1.0"
    assert "schema_" not in dumped
