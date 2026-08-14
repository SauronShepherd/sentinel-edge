from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel_edge.security import canonical_json_bytes, sha256_bytes


class PowerServiceState(StrEnum):
    HEALTHY = "healthy"
    DEGRADED_POWER = "degraded_power"
    RECOVERING = "recovering"


class EnergyEvidenceKind(StrEnum):
    PHYSICAL = "physical"
    PROXY = "proxy"


class PowerTelemetrySample(BaseModel):
    """One raw platform-health sample; current and historical flags stay separate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    observed_at: datetime
    temperature_c: float | None = None
    under_voltage_current: bool = False
    under_voltage_history: bool = False
    frequency_capped_current: bool = False
    frequency_capped_history: bool = False
    throttled_current: bool = False
    throttled_history: bool = False
    swap_total_mb: float = Field(default=0.0, ge=0.0)
    swap_used_mb: float = Field(default=0.0, ge=0.0)
    zram_used_mb: float = Field(default=0.0, ge=0.0)
    major_faults_delta: int = Field(default=0, ge=0)
    memory_psi_avg10: float = Field(default=0.0, ge=0.0)
    source: str = "fixture"

    @model_validator(mode="after")
    def validate_memory(self) -> "PowerTelemetrySample":
        if self.swap_used_mb > self.swap_total_mb and self.swap_total_mb > 0:
            raise ValueError("swap_used_mb cannot exceed swap_total_mb")
        if not self.source.strip():
            raise ValueError("power telemetry source must not be blank")
        return self

    @property
    def current_power_threat(self) -> bool:
        return self.under_voltage_current or self.frequency_capped_current or self.throttled_current

    @property
    def history_power_event(self) -> bool:
        return self.under_voltage_history or self.frequency_capped_history or self.throttled_history


class PowerHealthSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    state: PowerServiceState
    observed_samples: int = Field(ge=0)
    healthy_recovery_samples: int = Field(ge=0)
    required_recovery_samples: int = Field(gt=0)
    current: PowerTelemetrySample | None = None
    current_power_threat: bool
    historical_power_event_seen: bool
    reason_codes: tuple[str, ...]
    snapshot_digest: str


class EnergyMeasurement(BaseModel):
    """Physical energy or an explicitly labelled non-energy proxy."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: EnergyEvidenceKind
    source_class: Literal["measured", "fixture", "simulated"]
    scenario_window_id: str
    method: str
    quality_target_id: str
    quality_guardrail_passed: bool
    energy_j: float | None = Field(default=None, ge=0.0)
    proxy_value: float | None = Field(default=None, ge=0.0)
    proxy_unit: str | None = None
    sampling_hz: float | None = Field(default=None, gt=0.0)
    idle_energy_j: float | None = Field(default=None, ge=0.0)
    uncertainty_j: float | None = Field(default=None, ge=0.0)
    complete_node_scope: bool = False
    included_components: tuple[str, ...] = ()
    instrument_id: str | None = None
    meter_coverage_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    meter_alignment_ms: float | None = Field(default=None, ge=0.0)
    minimum_meter_coverage_fraction: float = Field(default=1.0, gt=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_energy_evidence(self) -> "EnergyMeasurement":
        for value in (self.scenario_window_id, self.method, self.quality_target_id):
            if not value.strip():
                raise ValueError("energy evidence identifiers must not be blank")
        if self.kind is EnergyEvidenceKind.PHYSICAL:
            if self.energy_j is None or self.sampling_hz is None or self.uncertainty_j is None:
                raise ValueError("physical energy requires energy_j, sampling_hz and uncertainty_j")
            if self.proxy_value is not None or self.proxy_unit is not None:
                raise ValueError("physical energy cannot also be a proxy")
            if not self.instrument_id or not self.instrument_id.strip():
                raise ValueError("physical energy requires an instrument identity")
            if self.meter_coverage_fraction is None or self.meter_alignment_ms is None:
                raise ValueError("physical energy requires meter coverage and alignment")
        else:
            if self.energy_j is not None:
                raise ValueError("a proxy must not populate energy_j")
            if self.proxy_value is None or not self.proxy_unit or not self.proxy_unit.strip():
                raise ValueError("a proxy requires proxy_value and proxy_unit")
        return self


def disclose_external_energy_method(measurement: EnergyMeasurement) -> dict[str, object]:
    """Return the auditable external-meter method and uncertainty disclosure."""
    if measurement.kind is not EnergyEvidenceKind.PHYSICAL:
        raise ValueError("external energy disclosure requires physical measurement")
    if "external" not in measurement.method.lower() or measurement.uncertainty_j is None:
        raise ValueError("external energy method and uncertainty must be disclosed")
    return {
        "method": measurement.method,
        "instrument_id": measurement.instrument_id,
        "sampling_hz": measurement.sampling_hz,
        "uncertainty_j": measurement.uncertainty_j,
        "meter_coverage_fraction": measurement.meter_coverage_fraction,
        "meter_alignment_ms": measurement.meter_alignment_ms,
        "complete_node_scope": measurement.complete_node_scope,
        "included_components": list(measurement.included_components),
    }


class PowerHealthMonitor:
    """Small deterministic state machine with explicit recovery hysteresis."""

    def __init__(self, *, required_recovery_samples: int = 3, history_limit: int = 256) -> None:
        if required_recovery_samples < 1 or history_limit < 1:
            raise ValueError("power monitor bounds must be positive")
        self.required_recovery_samples = required_recovery_samples
        self.history_limit = history_limit
        self._samples: list[PowerTelemetrySample] = []
        self._state = PowerServiceState.HEALTHY
        self._recovery = 0

    def observe(self, sample: PowerTelemetrySample) -> PowerHealthSnapshot:
        self._samples.append(sample)
        self._samples = self._samples[-self.history_limit :]
        if sample.current_power_threat:
            self._state = PowerServiceState.DEGRADED_POWER
            self._recovery = 0
        elif self._state in {PowerServiceState.DEGRADED_POWER, PowerServiceState.RECOVERING}:
            self._recovery += 1
            self._state = (
                PowerServiceState.HEALTHY
                if self._recovery >= self.required_recovery_samples
                else PowerServiceState.RECOVERING
            )
        return self.snapshot()

    def snapshot(self) -> PowerHealthSnapshot:
        current = self._samples[-1] if self._samples else None
        history_seen = any(sample.history_power_event or sample.current_power_threat for sample in self._samples)
        reasons: list[str] = []
        if current is None:
            reasons.append("power_telemetry_missing")
        else:
            if current.under_voltage_current:
                reasons.append("under_voltage_current")
            if current.frequency_capped_current:
                reasons.append("frequency_capped_current")
            if current.throttled_current:
                reasons.append("throttled_current")
            if self._state is PowerServiceState.RECOVERING:
                reasons.append("power_recovery_hysteresis_pending")
            if history_seen:
                reasons.append("historical_power_event_seen")
        if not reasons:
            reasons.append("power_health_normal")
        base = {
            "state": self._state.value,
            "observed_samples": len(self._samples),
            "healthy_recovery_samples": self._recovery,
            "required_recovery_samples": self.required_recovery_samples,
            "current": current.model_dump(mode="json") if current else None,
            "current_power_threat": bool(current and current.current_power_threat),
            "historical_power_event_seen": history_seen,
            "reason_codes": sorted(set(reasons)),
        }
        return PowerHealthSnapshot(**base, snapshot_digest=sha256_bytes(canonical_json_bytes(base)))

    def history(self) -> tuple[PowerTelemetrySample, ...]:
        return tuple(self._samples)


def benchmark_invalidation_reasons(
    sample: PowerTelemetrySample,
    *,
    maximum_memory_psi_avg10: float,
    maximum_major_faults_delta: int,
    invalidate_swap_use: bool = True,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if sample.under_voltage_current:
        reasons.append("under_voltage_current")
    if sample.frequency_capped_current:
        reasons.append("frequency_capped_current")
    if sample.throttled_current:
        reasons.append("throttled_current")
    if invalidate_swap_use and sample.swap_used_mb > 0:
        reasons.append("swap_in_use")
    if sample.major_faults_delta > maximum_major_faults_delta:
        reasons.append("major_faults_above_envelope")
    if sample.memory_psi_avg10 > maximum_memory_psi_avg10:
        reasons.append("memory_pressure_above_envelope")
    return tuple(sorted(set(reasons)))


def evaluate_energy_comparison(measurements: Iterable[EnergyMeasurement]) -> dict:
    values = tuple(measurements)
    failures: list[str] = []
    if not values:
        failures.append("energy_evidence_missing")
    quality_ids = {item.quality_target_id for item in values}
    if len(quality_ids) > 1:
        failures.append("quality_target_changed_between_variants")
    if any(not item.quality_guardrail_passed for item in values):
        failures.append("quality_guardrail_failed")
    kinds = {item.kind for item in values}
    if len(kinds) > 1:
        failures.append("physical_energy_and_proxy_mixed")
    physical = bool(values) and kinds == {EnergyEvidenceKind.PHYSICAL}
    physically_measured = physical and all(item.source_class == "measured" for item in values)
    if physical and any(not item.complete_node_scope for item in values):
        failures.append("complete_node_scope_not_proven")
    if physical and any(item.meter_coverage_fraction < item.minimum_meter_coverage_fraction for item in values):
        failures.append("meter_coverage_insufficient")
    if physical and any(item.meter_alignment_ms > 1000.0 for item in values):
        failures.append("meter_alignment_insufficient")
    base = {
        "schema": "sentinel-edge-energy-comparison/1.0",
        "sample_count": len(values),
        "evidence_kind": next(iter(kinds)).value if len(kinds) == 1 else "mixed_or_missing",
        "physical_energy_reportable": physically_measured and not failures,
        "headline_energy_j": (
            sum((item.energy_j or 0.0) - (item.idle_energy_j or 0.0) for item in values)
            if physically_measured and not failures
            else None
        ),
        "physical_format_present": physical,
        "source_classes": sorted({item.source_class for item in values}),
        "proxy_only": bool(values) and kinds == {EnergyEvidenceKind.PROXY},
        "fixed_quality_target": len(quality_ids) == 1 and bool(values),
        "quality_guardrails_passed": bool(values) and all(item.quality_guardrail_passed for item in values),
        "methods": sorted({item.method for item in values}),
        "sampling_hz": sorted({item.sampling_hz for item in values if item.sampling_hz is not None}),
        "idle_subtraction_disclosed": bool(values) and all(item.idle_energy_j is not None for item in values if item.kind is EnergyEvidenceKind.PHYSICAL),
        "uncertainty_disclosed": bool(values) and all(item.uncertainty_j is not None for item in values if item.kind is EnergyEvidenceKind.PHYSICAL),
        "meter_sample_coverage": [item.meter_coverage_fraction for item in values if item.meter_coverage_fraction is not None],
        "meter_alignment_ms": [item.meter_alignment_ms for item in values if item.meter_alignment_ms is not None],
        "failures": sorted(set(failures)),
        "limitations": [
            "A proxy is never labelled as physical energy.",
            "Complete-node scope is a declared measurement boundary and still requires target instrumentation qualification.",
        ],
    }
    return {**base, "report_digest": sha256_bytes(canonical_json_bytes(base))}
