from __future__ import annotations

import json
import tempfile
import weakref
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from pydantic import BaseModel, ConfigDict
from sentinel_edge import __version__

from sentinel_edge.analysis import AnalysisEnrichmentEngine
from sentinel_edge.audit import AuditCheckpointService
from sentinel_edge.collector import StreamingSourceCollector
from sentinel_edge.configuration import ConfigurationManager
from sentinel_edge.domain.models import (
    ConfigurationBundle,
    CriticalityTier,
    HazardKind,
    Observation,
    ResourceSnapshot,
    RuntimeMode,
    WorkloadSpec,
)
from sentinel_edge.incidents import IncidentEventEngine, IncidentIdentityService
from sentinel_edge.evidence import EvidenceTrustService
from sentinel_edge.exports import EvidenceExportService
from sentinel_edge.media import BoundedMediaParser
from sentinel_edge.operations import CapabilityMatrix
from sentinel_edge.privacy import PrivacyDispositionService
from sentinel_edge.security import KeyLifecycleRegistry, ProtectedLocalStateStore, SecretRegistry
from sentinel_edge.qualification import evaluate_readiness
from sentinel_edge.qualification.timing import build_latency_report
from sentinel_edge.runtime import TrustedTimeManager, VirtualClock, WorkloadScheduler
from sentinel_edge.storage import (
    ConfigurationStore,
    ContentAddressedArtifactStore,
    CriticalAnalysisSpool,
    IncidentJournalStore,
    SourceCursorStore,
    SpoolExhaustedError,
)


class ScenarioResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scenario_id: str
    observations: int
    analyses: int
    incident_versions: int
    authority_mutations: int
    dispatch_order: tuple[str, ...]
    final_states: dict[str, str]
    source_health: dict[str, str]
    opportunity_counts: dict[str, int]
    opportunity_balanced: bool
    notification_metrics: dict[str, int | float]
    schedule_digest: str
    trace_ids: dict[str, str]
    scheduler: dict[str, Any]
    critical_spool: dict[str, Any]
    storage: dict[str, Any]
    time_trust: dict[str, Any]
    timing_metrics: dict[str, dict[str, int | float | str]]
    latency_report: dict[str, dict[str, Any]]
    manifest_sha256: str | None = None


def _finalize_owned_resources(resources: tuple[Any, ...], temporary_artifacts: Any) -> None:
    """Best-effort fallback cleanup for engines used without a context manager."""
    for resource in resources:
        close = getattr(resource, "close", None)
        if close is not None:
            try:
                close()
            except Exception:
                pass
    if temporary_artifacts is not None:
        try:
            temporary_artifacts.cleanup()
        except Exception:
            pass


def default_configuration_bundle() -> ConfigurationBundle:
    return ConfigurationBundle(
        bundle_id="sentinel-default",
        version=__version__,
        actor="system-bootstrap",
        created_at=datetime(2026, 8, 2, 10, 0, tzinfo=timezone.utc),
        settings={
            "available_memory_mb": 512,
            "notification_budget": 8,
            "live_connectors_enabled": False,
            "critical_spool_max_items": 256,
            "critical_spool_max_bytes": 4 * 1024 * 1024,
            "critical_spool_max_age_seconds": 900,
            "artifact_max_bytes": 16 * 1024 * 1024,
            "artifact_reserve_bytes": 512 * 1024,
        },
        workloads=(
            WorkloadSpec(
                workload_id="earthquake-trigger",
                hazard=HazardKind.EARTHQUAKE,
                tier=CriticalityTier.A_IMMEDIATE,
                period_ms=10,
                deadline_ms=100,
                max_deferral_ms=0,
                estimated_cost_ms=5,
                memory_mb=16,
                profile_id="seismic-trigger-v1",
            ),
            WorkloadSpec(
                workload_id="wildfire-stage2",
                hazard=HazardKind.WILDFIRE,
                tier=CriticalityTier.B_URGENT,
                period_ms=1000,
                deadline_ms=1500,
                max_deferral_ms=2000,
                estimated_cost_ms=80,
                memory_mb=96,
                profile_id="wildfire-deterministic-v1",
                forced_scan_ms=5000,
            ),
            WorkloadSpec(
                workload_id="flood-evaluate",
                hazard=HazardKind.FLOOD,
                tier=CriticalityTier.C_TIMELY,
                period_ms=5000,
                deadline_ms=3000,
                max_deferral_ms=10000,
                estimated_cost_ms=15,
                memory_mb=24,
                profile_id="flood-rules-v2",
            ),
            WorkloadSpec(
                workload_id="landslide-evaluate",
                hazard=HazardKind.LANDSLIDE,
                tier=CriticalityTier.C_TIMELY,
                period_ms=5000,
                deadline_ms=3000,
                max_deferral_ms=10000,
                estimated_cost_ms=15,
                memory_mb=24,
                profile_id="landslide-rules-v2",
            ),
        ),
    )


class DeterministicScenarioEngine:
    def __init__(self, *, state_dir: str | Path | None = None, mode: RuntimeMode = RuntimeMode.JUDGE) -> None:
        self._state_dir = Path(state_dir) if state_dir else None
        self.mode = mode
        cursor_path = self._state_dir / "collector.sqlite3" if self._state_dir else ":memory:"
        incident_path = self._state_dir / "incidents.sqlite3" if self._state_dir else ":memory:"
        config_path = self._state_dir / "configuration.sqlite3" if self._state_dir else ":memory:"
        spool_path = self._state_dir / "critical-spool.sqlite3" if self._state_dir else ":memory:"
        disposition_path = self._state_dir / "disposition.sqlite3" if self._state_dir else ":memory:"
        secrets_path = self._state_dir / "secret-metadata.sqlite3" if self._state_dir else ":memory:"
        key_lifecycle_path = self._state_dir / "key-lifecycle.sqlite3" if self._state_dir else ":memory:"
        audit_path = self._state_dir / "audit-checkpoints.sqlite3" if self._state_dir else ":memory:"
        protected_state_path = self._state_dir / "protected-local-state.sqlite3" if self._state_dir else ":memory:"
        self._temp_artifacts = None
        if self._state_dir:
            artifact_path = self._state_dir / "artifacts"
        else:
            self._temp_artifacts = tempfile.TemporaryDirectory(prefix="sentinel-edge-artifacts-")
            artifact_path = Path(self._temp_artifacts.name)
        if self._state_dir:
            self._state_dir.mkdir(parents=True, exist_ok=True)
        self.clock = VirtualClock()
        self.time_trust = TrustedTimeManager()
        self.time_trust.register_fixture(now=self.clock.now_utc(), monotonic_ns=self.clock.monotonic_ns())
        self.collector = StreamingSourceCollector(buffer_capacity=64, cursor_store=SourceCursorStore(cursor_path))
        self.analysis = AnalysisEnrichmentEngine()
        self.artifacts = ContentAddressedArtifactStore(
            artifact_path, max_bytes=16 * 1024 * 1024, reserve_bytes=512 * 1024
        )
        self.configuration = ConfigurationManager(
            ConfigurationStore(config_path),
            self.artifacts,
        )
        if self.configuration.store.active() is None:
            activation = self.configuration.activate(default_configuration_bundle())
            if activation.state.value != "active":
                raise RuntimeError(f"default configuration failed: {activation.reason_codes}")
        active = self.configuration.store.active()
        assert active is not None
        approved = {item.profile_id for item in active.workloads}
        self.runtime = WorkloadScheduler(
            queue_limit=128,
            tier_a_reserve_memory_mb=64,
            clock=self.clock,
            mode=mode,
            approved_profile_ids=approved,
        )
        incident_store = IncidentJournalStore(incident_path)
        self.incidents = IncidentEventEngine(
            incident_store,
            notification_budget=int(active.settings.get("notification_budget", 8)),
        )
        self.evidence = EvidenceTrustService(incident_store, self.artifacts)
        self.disposition = PrivacyDispositionService(
            disposition_path, authority_recorder=incident_store.record_authority_mutation
        )
        self.evidence.set_disposition_service(self.disposition)
        self.secrets = SecretRegistry(secrets_path)
        self.key_lifecycle = KeyLifecycleRegistry(key_lifecycle_path)
        self.audit = AuditCheckpointService(self.key_lifecycle, audit_path)
        self.protected_state = ProtectedLocalStateStore(protected_state_path)
        self.media_parser = BoundedMediaParser()
        self.exports = EvidenceExportService(
            self.evidence,
            self.artifacts,
            disposition=self.disposition,
            authority_watermark_supplier=self.incidents.authority_conformance,
        )
        self.identity = IncidentIdentityService(incident_store)
        self.critical_spool = CriticalAnalysisSpool(
            spool_path,
            max_items=int(active.settings.get("critical_spool_max_items", 256)),
            max_bytes=int(active.settings.get("critical_spool_max_bytes", 4 * 1024 * 1024)),
            max_age_seconds=int(active.settings.get("critical_spool_max_age_seconds", 900)),
        )
        self._incident_authority_available = True
        self.capabilities = CapabilityMatrix()
        self._register_workloads(active.workloads)
        self.readiness = evaluate_readiness(
            mode=mode,
            active_configuration=True,
            incident_authority_available=True,
            artifact_store_writable=self.artifacts.health().writable,
            schema_compatible=bool(self.incidents.authority_conformance()["valid"] and self.incidents.projection_conformance()["valid"]),
            clock_usable=self.time_trust.snapshot.display_time_allowed,
            profile_ids_required={item.profile_id for item in active.workloads},
            profile_ids_admitted={item.profile_id for item in active.workloads},
            recovery_reconciled=not bool(self._state_dir and (self._state_dir / ".restore-required.json").exists()),
            physical_signal_required=False,
            target_host_required=False,
        )
        self._owned_resources = (
            self.critical_spool,
            self.secrets,
            self.key_lifecycle,
            self.audit,
            self.protected_state,
            self.configuration.store,
            self.collector._cursor_store,
            self.incidents._store,
            self.artifacts,
        )
        self._finalizer = weakref.finalize(
            self,
            _finalize_owned_resources,
            self._owned_resources,
            self._temp_artifacts,
        )

    def close(self) -> None:
        """Close resources owned by the scenario engine before state cleanup."""
        if getattr(self, "_closed", False):
            return
        self._finalizer.detach()
        for resource in self._owned_resources:
            close = getattr(resource, "close", None)
            if close is not None:
                close()
        temporary_artifacts = self._temp_artifacts
        self._temp_artifacts = None
        if temporary_artifacts is not None:
            temporary_artifacts.cleanup()
        self._closed = True

    def __del__(self) -> None:
        # Resource cleanup is registered with weakref.finalize.  Keeping this
        # method intentionally empty avoids a __del__ method delaying cyclic
        # collection until after TemporaryDirectory cleanup on Windows.
        return None

    def _register_workloads(self, specs: tuple[WorkloadSpec, ...]) -> None:
        for spec in specs:
            self.runtime.register(spec)

    def activate_configuration(self, raw: ConfigurationBundle | dict[str, Any], *, fail_canary: bool = False) -> Any:
        if self.runtime.queued or self.runtime.snapshot().active:
            raise RuntimeError("configuration activation requires an idle runtime")

        def canary(bundle: ConfigurationBundle) -> tuple[bool, tuple[str, ...]]:
            if fail_canary:
                return False, ("simulated_tier_a_regression",)
            try:
                probe = WorkloadScheduler(
                    queue_limit=self.runtime.queue_limit,
                    tier_a_reserve_memory_mb=self.runtime.tier_a_reserve_memory_mb,
                    clock=self.clock,
                    mode=self.runtime.mode,
                    approved_profile_ids={item.profile_id for item in bundle.workloads},
                )
                for spec in bundle.workloads:
                    probe.register(spec)
                expected_hazards = {item.value for item in HazardKind}
                observed_hazards = {item.hazard.value for item in bundle.workloads}
                if observed_hazards != expected_hazards:
                    return False, ("four_hazard_coverage_missing",)
            except (TypeError, ValueError) as exc:
                return False, (f"runtime_canary:{exc}",)
            return True, ("runtime_canary_passed",)

        record = self.configuration.activate(raw, canary=canary)
        if record.state.value == "active":
            active = self.configuration.store.active()
            assert active is not None
            self.runtime = WorkloadScheduler(
                queue_limit=128,
                tier_a_reserve_memory_mb=64,
                clock=self.clock,
                mode=self.runtime.mode,
                approved_profile_ids={item.profile_id for item in active.workloads},
            )
            self._register_workloads(active.workloads)
            self.incidents.notification_budget = int(active.settings.get("notification_budget", 8))
        return record

    def set_incident_authority_available(self, available: bool, *, reason: str = "operator_control") -> None:
        self._incident_authority_available = available
        if available:
            self.capabilities.set("incident_authority", "healthy", "authority_available")
        else:
            self.capabilities.set("incident_authority", "failed", reason, "critical_spool_active")

    def set_analysis_available(self, available: bool = True, *, reason: str = "operator_control") -> None:
        self.capabilities.set("analysis", "healthy" if available else "failed",
                              "analysis_available" if available else reason)

    def set_runtime_available(self, available: bool = True, *, reason: str = "operator_control") -> None:
        self.capabilities.set("runtime", "healthy" if available else "failed",
                              "runtime_available" if available else reason)

    def set_api_available(self, available: bool = True, *, reason: str = "operator_control") -> None:
        self.capabilities.set("api", "healthy" if available else "failed",
                              "api_available" if available else reason)

    def apply_or_spool(self, analysis: Any, accepted_at: datetime | None = None) -> Any:
        accepted_at = accepted_at or analysis.produced_at
        if self._incident_authority_available:
            return self.incidents.apply_analysis(analysis, accepted_at)
        try:
            self.critical_spool.enqueue(analysis, enqueued_at=accepted_at)
        except SpoolExhaustedError:
            self.capabilities.set("incident_authority", "failed", "critical_spool_exhausted")
            self.capabilities.set("evidence", "degraded", "critical_spool_exhausted")
            raise
        return None

    def recover_incident_authority(self, *, now: datetime | None = None) -> tuple[str, ...]:
        self._incident_authority_available = True
        delivered = self.critical_spool.drain(
            lambda analysis: self.incidents.apply_analysis(analysis, analysis.produced_at),
            now=now,
        )
        metrics = self.critical_spool.metrics(now=now)
        if metrics.pending_items:
            self.capabilities.set("incident_authority", "degraded", "critical_spool_not_drained")
        else:
            self.capabilities.set("incident_authority", "healthy", "critical_spool_reconciled")
        return delivered

    def set_storage_read_only(self, value: bool = True) -> None:
        self.artifacts.set_read_only(value)
        if value:
            self.capabilities.set("evidence", "degraded", "degraded_storage_read_only")
        else:
            self.capabilities.set("evidence", "healthy", "storage_writable")

    def run(self, scenario: dict[str, Any], *, manifest_sha256: str | None = None) -> ScenarioResult:
        if self.readiness.state.value != "ready":
            raise RuntimeError(f"startup readiness barrier is not ready: {self.readiness.reason_codes}")
        scenario_id = scenario["scenario_id"]
        observations: list[Observation] = []
        for raw in scenario["observations"]:
            source_id = raw["source_id"]
            sequence = raw["sequence"]
            correlation_id = uuid5(NAMESPACE_URL, f"sentinel:{scenario_id}:{source_id}:{sequence}")
            observation_id = uuid5(NAMESPACE_URL, f"sentinel-observation:{scenario_id}:{source_id}:{sequence}")
            observations.append(Observation.model_validate({**raw, "correlation_id": correlation_id, "observation_id": observation_id}))
        observations.sort(key=lambda item: (item.received_at, item.source_id, item.sequence))
        if observations:
            self.clock = VirtualClock(observations[0].received_at)
            self.runtime.clock = self.clock
            self.time_trust = TrustedTimeManager()
            self.time_trust.register_fixture(now=self.clock.now_utc(), monotonic_ns=self.clock.monotonic_ns())
        workload_by_hazard = {
            HazardKind.EARTHQUAKE: "earthquake-trigger",
            HazardKind.WILDFIRE: "wildfire-stage2",
            HazardKind.FLOOD: "flood-evaluate",
            HazardKind.LANDSLIDE: "landslide-evaluate",
        }
        analyses = []
        previous_received: datetime | None = None
        traces: dict[str, str] = {}
        timing_metrics: dict[str, dict[str, int | float | str]] = {}
        for observation in observations:
            if previous_received is not None:
                delta_ms = max(0, int((observation.received_at - previous_received).total_seconds() * 1000))
                self.clock.advance_ms(delta_ms)
            previous_received = observation.received_at
            self.collector.ingest(observation)
            ingest_at = self.clock.now_utc()
            self.runtime.submit(
                workload_by_hazard[observation.hazard],
                {"observation_id": str(observation.observation_id)},
                observation.received_at,
                scheduled_release_at=observation.received_at,
                captured_at=observation.observed_at,
                correlation_id=observation.correlation_id,
            )
            analysis = self.analysis.analyze(observation)
            analyses.append(analysis)
            decision_at = self.clock.now_utc()
            timing_metrics[observation.source_id] = {
                "capture_at": observation.observed_at.isoformat(),
                "ingest_at": ingest_at.isoformat(),
                "release_at": observation.received_at.isoformat(),
                "decision_at": decision_at.isoformat(),
                "acquisition_delay_ms": max(0.0, (observation.received_at - observation.observed_at).total_seconds() * 1000),
                "queue_age_ms": max(0.0, (decision_at - observation.received_at).total_seconds() * 1000),
            }
            incident = self.apply_or_spool(analysis, observation.received_at)
            if incident is not None:
                traces[observation.source_id] = str(incident.correlation_ids[-1])
        resources = ResourceSnapshot.model_validate(scenario.get("resources", {
            "cpu_pressure": 0.4, "memory_pressure": 0.4, "io_pressure": 0.2,
            "temperature_c": 55.0, "available_memory_mb": 512, "power_degraded": False,
        }))
        dispatch_order: list[str] = []
        while self.runtime.queued:
            job = self.runtime.dispatch(resources)
            if job is None:
                self.capabilities.set("runtime", "degraded", "admission_stalled")
                break
            dispatch_order.append(job.workload.workload_id)
            self.clock.advance_ms(job.workload.estimated_cost_ms)
            self.runtime.complete(job)
        reconciliation = self.runtime.opportunities.reconcile()
        snapshot = self.runtime.snapshot()
        return ScenarioResult(
            scenario_id=scenario_id,
            observations=len(observations),
            analyses=len(analyses),
            incident_versions=len(self.incidents.journal()),
            authority_mutations=len(self.incidents.authority_journal()),
            dispatch_order=tuple(dispatch_order),
            final_states={item.hazard.value: item.state.value for item in self.incidents.current()},
            source_health={item.source_id: item.state.value for item in self.collector.health()},
            opportunity_counts=self.runtime.opportunities.counts(),
            opportunity_balanced=bool(reconciliation["balanced"]),
            notification_metrics=self.incidents.notification_metrics(self.clock.now_utc()),
            schedule_digest=self.runtime.opportunities.schedule_digest(),
            trace_ids=traces,
            scheduler=snapshot.model_dump(mode="json"),
            critical_spool=self.critical_spool.metrics(now=self.clock.now_utc()).__dict__,
            storage=self.artifacts.usage_report(),
            time_trust=self.time_trust.snapshot.model_dump(mode="json"),
            timing_metrics=timing_metrics,
            latency_report=build_latency_report(timing_metrics),
            manifest_sha256=manifest_sha256,
        )


def load_scenario(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
