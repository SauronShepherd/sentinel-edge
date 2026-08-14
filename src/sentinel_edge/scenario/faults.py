"""Declared deterministic scenario fault injection and recovery reporting."""

from __future__ import annotations

from datetime import timedelta
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from sentinel_edge.domain.models import HealthState
from sentinel_edge.scenario.engine import DeterministicScenarioEngine


class FaultKind(StrEnum):
    SENSOR = "sensor"
    CLOCK = "clock"
    WORKER = "worker"
    SOURCE = "source"
    STORAGE = "storage"


class FaultResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fault: FaultKind
    injected: bool
    expected_state: str
    reason_code: str
    recovered: bool = False


def inject_fault(
    engine: DeterministicScenarioEngine,
    fault: FaultKind,
    *,
    source_id: str | None = None,
) -> FaultResult:
    """Apply one declared fault through the owning component's public hook."""
    if fault is FaultKind.SENSOR:
        if source_id is None:
            raise ValueError("sensor fault requires source_id")
        engine.collector.mark_stale(engine.clock.now_utc() + timedelta(minutes=1), threshold_seconds=30)
        return FaultResult(fault=fault, injected=True, expected_state=HealthState.STALE.value, reason_code="timeout")
    if fault is FaultKind.SOURCE:
        if source_id is None:
            raise ValueError("source fault requires source_id")
        engine.collector.mark_failed(source_id, "transport_lost", engine.clock.now_utc())
        return FaultResult(fault=fault, injected=True, expected_state=HealthState.FAILED.value, reason_code="transport_lost")
    if fault is FaultKind.CLOCK:
        engine.clock.step_utc(timedelta(hours=-1))
        engine.capabilities.set("runtime", "degraded", "clock_step_injected")
        return FaultResult(fault=fault, injected=True, expected_state="degraded", reason_code="clock_step_injected")
    if fault is FaultKind.WORKER:
        engine.capabilities.set("analysis", "degraded", "worker_crash_injected")
        return FaultResult(fault=fault, injected=True, expected_state="degraded", reason_code="worker_crash_injected")
    engine.set_storage_read_only(True)
    return FaultResult(fault=fault, injected=True, expected_state="degraded", reason_code="degraded_storage_read_only")


def recover_fault(
    engine: DeterministicScenarioEngine,
    fault: FaultKind,
    *,
    source_id: str | None = None,
) -> FaultResult:
    """Restore only reversible scenario faults and report the recovery contract."""
    if fault is FaultKind.SOURCE:
        if source_id is None:
            raise ValueError("source recovery requires source_id")
        engine.collector.mark_failed(source_id, "recovery_probe", engine.clock.now_utc())
        return FaultResult(fault=fault, injected=False, expected_state=HealthState.FAILED.value, reason_code="recovery_requires_new_observation", recovered=False)
    if fault is FaultKind.STORAGE:
        engine.set_storage_read_only(False)
        return FaultResult(fault=fault, injected=False, expected_state=HealthState.HEALTHY.value, reason_code="storage_writable", recovered=True)
    if fault is FaultKind.WORKER:
        engine.capabilities.set("analysis", "healthy", "worker_recovered")
        return FaultResult(fault=fault, injected=False, expected_state=HealthState.HEALTHY.value, reason_code="worker_recovered", recovered=True)
    if fault is FaultKind.CLOCK:
        engine.capabilities.set("runtime", "healthy", "clock_reconciled")
        return FaultResult(fault=fault, injected=False, expected_state=HealthState.HEALTHY.value, reason_code="clock_reconciled", recovered=True)
    return FaultResult(fault=fault, injected=False, expected_state=HealthState.STALE.value, reason_code="sensor_requires_new_observation", recovered=False)
