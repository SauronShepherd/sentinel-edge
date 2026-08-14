from __future__ import annotations

from sentinel_edge.domain.models import CapabilityRecord, HealthState


class CapabilityMatrix:
    """Explicit operational capabilities; no generic healthy flag can hide a critical loss."""

    DEFAULTS = {
        "acquisition": "local observations can be accepted and durably watermarked",
        "analysis": "hazard observations can be interpreted",
        "runtime": "workloads can be admitted and scheduled",
        "incident_authority": "incident lifecycle can be updated and recovered",
        "api": "supported client projections can be served",
        "evidence": "evidence artifacts can be persisted and verified",
    }

    def __init__(self) -> None:
        self._records = {
            key: CapabilityRecord(capability_id=key, state=HealthState.HEALTHY, consequence=value)
            for key, value in self.DEFAULTS.items()
        }

    def set(self, capability_id: str, state: HealthState | str, *reason_codes: str) -> None:
        state = HealthState(state)
        if capability_id not in self._records:
            raise KeyError(capability_id)
        current = self._records[capability_id]
        self._records[capability_id] = current.model_copy(
            update={"state": state, "reason_codes": tuple(sorted(set(reason_codes)))}
        )

    def records(self) -> tuple[CapabilityRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))

    @property
    def overall(self) -> HealthState:
        states = {record.state for record in self._records.values()}
        if HealthState.FAILED in states:
            return HealthState.FAILED
        if states & {HealthState.DEGRADED, HealthState.STALE, HealthState.UNKNOWN}:
            return HealthState.DEGRADED
        return HealthState.HEALTHY
