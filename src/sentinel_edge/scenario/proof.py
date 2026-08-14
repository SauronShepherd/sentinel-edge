"""Candidate-facing deterministic simultaneous-event proof campaign.

This module deliberately composes the existing Component-1 collector,
Component-2 analyzers, Component-3 scheduler and Component-4 incident/evidence
services.  It does not add a scenario-only incident authority.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from sentinel_edge.domain.models import (
    EvidenceItem,
    EvidenceRetentionState,
    ExtractionConfidenceState,
    HazardKind,
    HealthState,
    MediaIntegrityState,
    Observation,
    ParserIsolationState,
    ResourceSnapshot,
    RuntimeMode,
    SourceMode,
    SourceStanding,
)
from sentinel_edge.runtime import WorkloadScheduler
from sentinel_edge.scenario.engine import DeterministicScenarioEngine
from sentinel_edge.scenario.faults import FaultKind, inject_fault, recover_fault
from sentinel_edge.scenario.replay import ReplayMode, compare_replays, replay_scenario
from sentinel_edge.security import canonical_json_bytes, sha256_bytes
from sentinel_edge.storage import ArtifactPolicy


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _normal_variant(scenario: dict[str, Any]) -> dict[str, Any]:
    safe_values = {
        "earthquake": {"accel_x": 0.0, "accel_y": 0.0, "accel_z": 1.0},
        "wildfire": {"smoke_score": 0.05, "flame_score": 0.0, "temporal_persistence": 0.2},
        "flood": {"water_level_m": 0.2, "rate_of_rise_m_per_h": 0.01, "rainfall_mm_h": 1.0},
        "landslide": {
            "soil_moisture_fraction": 0.3,
            "tilt_rate_deg_h": 0.01,
            "vibration_rms": 0.01,
            "rainfall_mm_h": 1.0,
        },
    }
    clone = json.loads(json.dumps(scenario))
    clone["scenario_id"] = f"{scenario['scenario_id']}-normal-phase"
    for raw in clone.get("observations", []):
        raw["values"] = safe_values[raw["hazard"]]
    clone["resources"] = {
        "cpu_pressure": 0.25,
        "memory_pressure": 0.25,
        "io_pressure": 0.15,
        "temperature_c": 52.0,
        "available_memory_mb": 512,
        "power_degraded": False,
    }
    return clone


def _observation_from_raw(raw: dict[str, Any], scenario_id: str, *, sequence: int | None = None,
                          observed_at: datetime | None = None, received_at: datetime | None = None,
                          source_mode: SourceMode | None = None, source_id: str | None = None) -> Observation:
    seq = int(sequence if sequence is not None else raw["sequence"])
    source_id = str(source_id if source_id is not None else raw["source_id"])
    correlation_id = uuid5(NAMESPACE_URL, f"sentinel:{scenario_id}:{source_id}:{seq}")
    observation_id = uuid5(NAMESPACE_URL, f"sentinel-observation:{scenario_id}:{source_id}:{seq}")
    payload = {
        **raw,
        "source_id": source_id,
        "sequence": seq,
        "correlation_id": correlation_id,
        "observation_id": observation_id,
    }
    if observed_at is not None:
        payload["observed_at"] = observed_at
    if received_at is not None:
        payload["received_at"] = received_at
    if source_mode is not None:
        payload["source_mode"] = source_mode
    return Observation.model_validate(payload)


def _proof_invariants(proof: dict[str, Any]) -> dict[str, bool]:
    phase = proof["trigger_phase"]
    faults = proof["fault_campaign"]
    scheduler = proof["scheduler_campaign"]
    return {
        "normal_multi_hazard_monitoring": all(v in {"normal", "watch"} for v in proof["normal_phase"]["final_states"].values()),
        "smoke_observation_present": proof["scenario_inputs"]["smoke_score"] >= 0.5,
        "heavy_rain_present": proof["scenario_inputs"]["rainfall_mm_h"] >= 20.0,
        "rising_water_present": proof["scenario_inputs"]["rate_of_rise_m_per_h"] > 0.0,
        "slope_instability_present": proof["scenario_inputs"]["tilt_rate_deg_h"] > 0.0,
        "earthquake_trigger_present": proof["scenario_inputs"]["dynamic_imu_present"],
        "tier_a_reserved_first": bool(phase["dispatch_order"]) and phase["dispatch_order"][0] == "earthquake-trigger",
        "wildfire_wake_sleep_visible": scheduler["wildfire_forced_scan"]["processed"] and "wildfire-stage2" in scheduler["wildfire_forced_scan"]["sleeping_after"],
        "flood_landslide_cadence_adapted": scheduler["cadence_adaptation"]["flood_period_after_ms"] < scheduler["cadence_adaptation"]["flood_period_before_ms"] and scheduler["cadence_adaptation"]["landslide_period_after_ms"] < scheduler["cadence_adaptation"]["landslide_period_before_ms"],
        "bounded_queue_declared": scheduler["queue_limit"] == 128,
        "workload_deferral_visible": "flood-evaluate" in scheduler["deferral"]["deferred_before_release"],
        "overload_visible": scheduler["deferral"]["overloaded"],
        "network_source_failure_visible": faults["source_failure"]["injected"] and faults["source_failure"]["recovered_after_new_observation"],
        "sensor_failure_missingness_visible": faults["sensor_failure"]["injected"] and faults["sensor_failure"]["state_after"] == "stale",
        "worker_crash_recovery_visible": faults["worker_crash"]["injected"] and faults["worker_crash"]["recovered"],
        "replay_cannot_be_fresh": faults["replay_backfill"]["replay_rejected"] and faults["replay_backfill"]["backfill_zero_contribution"],
        "evidence_created": proof["evidence"]["count"] >= 1 and bool(proof["evidence"]["sha256"]),
        "component_4_incident_transitions": phase["authority_mutations"] >= phase["incident_versions"] > 0,
        "ui_projection_data_available": len(phase["final_states"]) == 4 and bool(phase["scheduler"]),
        "component_5_projection_verified": proof["component_5_projection"]["status_code"] == 200 and proof["component_5_projection"]["hazard_count"] == 4 and proof["component_5_projection"]["runtime_status_code"] == 200,
        "deterministic_reset_replay": proof["determinism"]["passed"],
        "storage_fault_recovered": faults["storage_pressure"]["injected"] and faults["storage_pressure"]["recovered"],
        "clock_fault_recovered": faults["clock_fault"]["injected"] and faults["clock_fault"]["recovered"],
        "thermal_power_pressure_visible": scheduler["deferral"]["resource_snapshot"]["temperature_c"] >= 82.0 and scheduler["deferral"]["resource_snapshot"]["power_degraded"],
    }


def run_submission_scenario_proof(
    scenario: dict[str, Any],
    *,
    manifest_sha256: str | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Run the complete no-hardware H0 scenario proof as a deterministic campaign."""
    # 1. Normal four-hazard monitoring, separately reset from the trigger run.
    with DeterministicScenarioEngine(mode=RuntimeMode.JUDGE) as normal_engine:
        normal = normal_engine.run(_normal_variant(scenario))

    # 2. Trigger phase through the ordinary production component contracts.
    with DeterministicScenarioEngine(mode=RuntimeMode.JUDGE) as trigger_engine:
        triggered = trigger_engine.run(scenario, manifest_sha256=manifest_sha256)
        wildfire_incident = next(item for item in trigger_engine.incidents.current() if item.hazard is HazardKind.WILDFIRE)
        artifact = trigger_engine.artifacts.put_bytes(
            b"sentinel-edge-deterministic-wildfire-trigger-evidence-v1",
            media_type="application/vnd.sentinel-edge.fixture",
            policy=ArtifactPolicy.incident_evidence(),
        )
        evidence_received_at = _dt(next(
            raw["received_at"] for raw in scenario["observations"] if raw["hazard"] == "wildfire"
        ))
        evidence = trigger_engine.evidence.ingest(EvidenceItem(
            evidence_id=uuid5(NAMESPACE_URL, f"sentinel-evidence:{scenario['scenario_id']}:wildfire-trigger-v1"),
            incident_id=wildfire_incident.incident_id,
            hazard=HazardKind.WILDFIRE,
            source_id="camera-1",
            source_standing=SourceStanding.FIRST_PARTY,
            media_integrity=MediaIntegrityState.ORIGINAL_VERIFIED,
            extraction_confidence_state=ExtractionConfidenceState.VERIFIED,
            extraction_confidence=1.0,
            freshness_state=HealthState.HEALTHY,
            claim_text="Deterministic smoke-like fixture evidence",
            content_sha256=artifact.sha256,
            origin_key="simultaneous-event-wildfire-trigger-v1",
            retention_state=EvidenceRetentionState.RETAINED,
            parser_state=ParserIsolationState.SANDBOXED,
            rights_basis="bundled-fixture",
            modality="fixture",
            received_at=evidence_received_at,
        ))
        # Component 5 proof: read the exact Component-4 state and Component-3 runtime
        # through the supported REST boundary used by the local client.
        from fastapi.testclient import TestClient
        from sentinel_edge.gateway import create_app

        with TestClient(create_app(trigger_engine)) as client:
            headers = {"Authorization": "Bearer sentinel-dev-viewer-token"}
            incident_response = client.get("/v1/incidents", headers=headers)
            runtime_response = client.get("/v1/runtime", headers=headers)
            incident_payload = incident_response.json() if incident_response.status_code == 200 else {}
            api_projection = {
                "transport": "local_component_5_rest",
                "status_code": incident_response.status_code,
                "runtime_status_code": runtime_response.status_code,
                "hazard_count": len(incident_payload) if isinstance(incident_payload, list) else len(incident_payload.get("incidents", [])) if isinstance(incident_payload, dict) else 0,
                "incident_authority_header": incident_response.headers.get("X-Incident-Authority"),
                "projection_header": incident_response.headers.get("X-Incident-Projection"),
            }

    # 3. Reset/replay determinism proof.
    replay_runs = tuple(replay_scenario(scenario, mode=mode) for mode in ReplayMode)
    replay_comparison = compare_replays(*replay_runs)

    # 4. Fault/recovery campaign. Faults act through declared component hooks.
    with DeterministicScenarioEngine(mode=RuntimeMode.DEVELOPMENT) as fault_engine:
        fault_engine.run(scenario)
        sensor_fault = inject_fault(fault_engine, FaultKind.SENSOR, source_id="camera-1")
        sensor_state = next(item.state.value for item in fault_engine.collector.health() if item.source_id == "camera-1")

        source_fault = inject_fault(fault_engine, FaultKind.SOURCE, source_id="hydro-1")
        source_probe = recover_fault(fault_engine, FaultKind.SOURCE, source_id="hydro-1")
        hydro_raw = next(item for item in scenario["observations"] if item["source_id"] == "hydro-1")
        recovery_time = max(fault_engine.clock.now_utc(), _dt(hydro_raw["received_at"])) + timedelta(seconds=1)
        recovered_hydro = _observation_from_raw(
            hydro_raw,
            scenario["scenario_id"],
            sequence=int(hydro_raw["sequence"]) + 1,
            observed_at=recovery_time,
            received_at=recovery_time,
        )
        fault_engine.collector.ingest(recovered_hydro)
        source_state_after = next(item for item in fault_engine.collector.health() if item.source_id == "hydro-1")

        worker_fault = inject_fault(fault_engine, FaultKind.WORKER)
        worker_recovery = recover_fault(fault_engine, FaultKind.WORKER)
        clock_fault = inject_fault(fault_engine, FaultKind.CLOCK)
        clock_recovery = recover_fault(fault_engine, FaultKind.CLOCK)
        storage_fault = inject_fault(fault_engine, FaultKind.STORAGE)
        storage_recovery = recover_fault(fault_engine, FaultKind.STORAGE)

        replay_raw = next(item for item in scenario["observations"] if item["source_id"] == "camera-1")
        replay_observation = _observation_from_raw(
            replay_raw,
            scenario["scenario_id"],
            sequence=99,
            source_mode=SourceMode.REPLAYED,
        )
        replay_rejected = False
        replay_reason = None
        try:
            fault_engine.collector.ingest(replay_observation)
        except ValueError as exc:
            replay_rejected = "replayed observations" in str(exc)
            replay_reason = str(exc)

        backfill_time = fault_engine.clock.now_utc()
        old_event_time = backfill_time - timedelta(hours=6)
        backfill = _observation_from_raw(
            replay_raw,
            f"{scenario['scenario_id']}-backfill",
            sequence=100,
            observed_at=old_event_time,
            received_at=backfill_time,
            source_mode=SourceMode.FIXTURE,
            source_id="camera-backfill",
        )
        fault_engine.collector.ingest(backfill)
        backfill_analysis = fault_engine.analysis.analyze(backfill)
        backfill_incident = fault_engine.apply_or_spool(backfill_analysis, backfill.received_at)

        fault_payload = {
            "sensor_failure": {
                "injected": sensor_fault.injected,
                "reason_code": sensor_fault.reason_code,
                "state_after": sensor_state,
            },
            "source_failure": {
                "injection_mode": "deterministic_simulated_transport_loss",
                "injected": source_fault.injected,
                "reason_code": source_fault.reason_code,
                "recovery_probe_requires_new_observation": not source_probe.recovered,
                "recovered_after_new_observation": source_state_after.state is HealthState.HEALTHY,
                "recovery_reason_codes": list(source_state_after.reason_codes),
            },
            "worker_crash": {
                "injection_mode": "deterministic_simulated_worker_failure",
                "injected": worker_fault.injected,
                "recovered": worker_recovery.recovered,
                "reason_codes": [worker_fault.reason_code, worker_recovery.reason_code],
            },
            "clock_fault": {
                "injected": clock_fault.injected,
                "recovered": clock_recovery.recovered,
                "reason_codes": [clock_fault.reason_code, clock_recovery.reason_code],
            },
            "storage_pressure": {
                "injected": storage_fault.injected,
                "recovered": storage_recovery.recovered,
                "reason_codes": [storage_fault.reason_code, storage_recovery.reason_code],
            },
            "replay_backfill": {
                "replay_rejected": replay_rejected,
                "replay_reason": replay_reason,
                "backfill_capture_age_ms": backfill.capture_age_ms,
                "backfill_zero_contribution": backfill_analysis.score == 0.0 and "source_ttl_expired_zero_contribution" in backfill_analysis.reason_codes,
                "backfill_incident_state": backfill_incident.state.value if backfill_incident is not None else None,
                "backfill_source_health": next(item.state.value for item in fault_engine.collector.health() if item.source_id == "camera-backfill"),
            },
        }

    # 5. Scheduler policy campaign, including thermal/power overload and recovery.
    with DeterministicScenarioEngine(mode=RuntimeMode.DEVELOPMENT) as scheduler_engine:
        before = {item.workload_id: item.period_ms for item in scheduler_engine.runtime.registry}
        # Heavy rain is fresh scenario context and changes only future cadence.
        flood_after = scheduler_engine.runtime.reallocate_cadence(
            "flood-evaluate", multiplier=2.0, reason_code="fresh_heavy_rainfall_context"
        )
        landslide_after = scheduler_engine.runtime.reallocate_cadence(
            "landslide-evaluate", multiplier=2.0, reason_code="fresh_heavy_rainfall_context"
        )

        pressure = ResourceSnapshot(
            cpu_pressure=0.96,
            memory_pressure=0.88,
            io_pressure=0.45,
            temperature_c=86.0,
            available_memory_mb=512,
            power_degraded=True,
        )
        scheduler_engine.runtime.submit("flood-evaluate", {"proof": "deferral"}, scheduler_engine.clock.now_utc())
        first_dispatch = scheduler_engine.runtime.dispatch(pressure)
        deferred_snapshot = scheduler_engine.runtime.snapshot()
        scheduler_engine.clock.advance_ms(flood_after.max_deferral_ms + 1)
        released = scheduler_engine.runtime.dispatch(pressure)
        if released is not None:
            scheduler_engine.clock.advance_ms(released.workload.estimated_cost_ms)
            scheduler_engine.runtime.complete(released)

        scheduler_engine.runtime.submit("wildfire-stage2", {"proof": "forced_scan"}, scheduler_engine.clock.now_utc())
        scheduler_engine.clock.advance_ms(5001)
        wildfire_job = scheduler_engine.runtime.dispatch(pressure)
        wildfire_processed = wildfire_job is not None and wildfire_job.workload.workload_id == "wildfire-stage2"
        if wildfire_job is not None:
            scheduler_engine.clock.advance_ms(wildfire_job.workload.estimated_cost_ms)
            scheduler_engine.runtime.complete(wildfire_job)
        forced_snapshot = scheduler_engine.runtime.snapshot()

        scheduler_payload = {
            "queue_limit": scheduler_engine.runtime.queue_limit,
            "cadence_adaptation": {
                "reason_code": "fresh_heavy_rainfall_context",
                "flood_period_before_ms": before["flood-evaluate"],
                "flood_period_after_ms": flood_after.period_ms,
                "landslide_period_before_ms": before["landslide-evaluate"],
                "landslide_period_after_ms": landslide_after.period_ms,
            },
            "deferral": {
                "first_dispatch_was_none": first_dispatch is None,
                "deferred_before_release": list(deferred_snapshot.deferred),
                "overloaded": deferred_snapshot.overloaded,
                "reason_codes": list(deferred_snapshot.reason_codes),
                "released_after_max_deferral": released is not None,
                "resource_snapshot": pressure.model_dump(mode="json"),
            },
            "wildfire_forced_scan": {
                "processed": wildfire_processed,
                "reason_codes": list(forced_snapshot.reason_codes),
                "sleeping_after": list(forced_snapshot.sleeping),
            },
            "fallback_schedule": list(scheduler_engine.runtime.fallback_schedule()),
        }

    raw_by_hazard = {item["hazard"]: item for item in scenario["observations"]}
    proof: dict[str, Any] = {
        "schema": "sentinel-edge.simultaneous-event-proof.v1",
        "scenario_id": scenario["scenario_id"],
        "manifest_sha256": manifest_sha256,
        "source_mode": "deterministic_simulated_fixture",
        "claim_class": "simulated",
        "physical_hardware_required": False,
        "physical_sensors_required": False,
        "component_boundaries": {
            "acquisition": "Component 1 — Streaming Source Collector",
            "analysis": "Component 2 — Analysis & Enrichment Engine",
            "runtime": "Component 3 — Model & Workload Runtime",
            "incident_authority": "Component 4 — Incident & Event Engine",
            "client_boundary": "Component 5 — REST API & Integration Gateway",
        },
        "scenario_inputs": {
            "smoke_score": raw_by_hazard["wildfire"]["values"].get("smoke_score", 0.0),
            "rainfall_mm_h": max(raw_by_hazard["flood"]["values"].get("rainfall_mm_h", 0.0), raw_by_hazard["landslide"]["values"].get("rainfall_mm_h", 0.0)),
            "rate_of_rise_m_per_h": raw_by_hazard["flood"]["values"].get("rate_of_rise_m_per_h", 0.0),
            "tilt_rate_deg_h": raw_by_hazard["landslide"]["values"].get("tilt_rate_deg_h", 0.0),
            "dynamic_imu_present": any(abs(raw_by_hazard["earthquake"]["values"].get(k, 0.0)) > 0.2 for k in ("accel_x", "accel_y")),
        },
        "normal_phase": normal.model_dump(mode="json"),
        "trigger_phase": triggered.model_dump(mode="json"),
        "component_5_projection": api_projection,
        "scheduler_campaign": scheduler_payload,
        "fault_campaign": fault_payload,
        "evidence": {
            "count": 1,
            "evidence_id": str(evidence.evidence_id),
            "sha256": evidence.content_sha256,
            "incident_id": str(evidence.incident_id),
            "source_id": evidence.source_id,
        },
        "determinism": replay_comparison.model_dump(mode="json"),
    }
    invariants = _proof_invariants(proof)
    proof["invariants"] = invariants
    proof["all_invariants_passed"] = all(invariants.values())
    transcript = {
        "scenario_id": scenario["scenario_id"],
        "manifest_sha256": manifest_sha256,
        "dispatch_order": list(triggered.dispatch_order),
        "timing_metrics": triggered.timing_metrics,
        "component_5_projection": api_projection,
        "fault_campaign": fault_payload,
        "scheduler_campaign": scheduler_payload,
        "evidence": proof["evidence"],
        "determinism": proof["determinism"],
    }
    proof["transcript_sha256"] = sha256_bytes(canonical_json_bytes(transcript))
    proof["invariant_report_sha256"] = sha256_bytes(canonical_json_bytes(invariants))

    if output_dir is not None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "transcript.json").write_text(json.dumps(transcript, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (out / "invariants.json").write_text(json.dumps(invariants, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (out / "proof.json").write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        proof["artifacts"] = {
            "transcript": (out / "transcript.json").as_posix(),
            "invariants": (out / "invariants.json").as_posix(),
            "proof": (out / "proof.json").as_posix(),
        }
    return proof
