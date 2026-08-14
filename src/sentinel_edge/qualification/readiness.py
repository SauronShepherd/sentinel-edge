from __future__ import annotations

from sentinel_edge.domain.models import ReadinessReport, ReadinessState, RuntimeMode


def evaluate_readiness(
    *,
    mode: RuntimeMode,
    active_configuration: bool,
    incident_authority_available: bool,
    artifact_store_writable: bool,
    schema_compatible: bool = True,
    clock_usable: bool = True,
    minimum_coverage: bool = True,
    recovery_reconciled: bool = True,
    profile_ids_required: set[str],
    profile_ids_admitted: set[str],
    physical_signal_required: bool = False,
    physical_signal_qualified: bool = False,
    target_host_required: bool = False,
    target_host_qualified: bool = False,
) -> ReadinessReport:
    checks = {
        "active_configuration": active_configuration,
        "incident_authority_available": incident_authority_available,
        "artifact_store_writable": artifact_store_writable,
        "schema_compatible": schema_compatible,
        "clock_usable": clock_usable,
        "minimum_coverage": minimum_coverage,
        "recovery_reconciled": recovery_reconciled,
        "runtime_profiles_complete": profile_ids_required <= profile_ids_admitted,
        "physical_signal_qualified": (not physical_signal_required) or physical_signal_qualified,
        "target_host_qualified": (not target_host_required) or target_host_qualified,
    }
    reasons = [name for name, passed in checks.items() if not passed]
    critical = {
        "active_configuration",
        "incident_authority_available",
        "artifact_store_writable",
        "schema_compatible",
        "clock_usable",
        "minimum_coverage",
        "recovery_reconciled",
        "runtime_profiles_complete",
    }
    if mode in {RuntimeMode.JUDGE, RuntimeMode.BENCHMARK}:
        critical |= {"physical_signal_qualified", "target_host_qualified"}
    state = ReadinessState.READY
    if any(name in critical for name in reasons):
        state = ReadinessState.BLOCKED
    elif reasons:
        state = ReadinessState.DEGRADED
    return ReadinessReport(
        state=state,
        mode=mode,
        checks=checks,
        reason_codes=tuple(sorted(reasons)) if reasons else ("readiness_barrier_passed",),
    )
