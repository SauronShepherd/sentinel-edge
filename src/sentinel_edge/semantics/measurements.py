from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from pydantic import BaseModel, ConfigDict

from sentinel_edge.domain.models import (
    MeasurementQuality,
    MeasurementStatistic,
    MeasurementValue,
    Observation,
)


@dataclass(frozen=True)
class PropertyDefinition:
    property_id: str
    allowed_units: frozenset[str]
    minimum: float | None = None
    maximum: float | None = None
    statistic: MeasurementStatistic | None = None
    requires_reference: bool = False
    requires_orientation: bool = False
    allowed_axes: frozenset[str] = frozenset()


class MeasurementContractReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    valid: bool
    usable_properties: tuple[str, ...]
    invalid_properties: tuple[str, ...]
    suspect_properties: tuple[str, ...]
    fusion_allowed: bool
    reason_codes: tuple[str, ...]


_DEFAULTS = (
    PropertyDefinition("smoke_score", frozenset({"ratio"}), 0.0, 1.0),
    PropertyDefinition("flame_score", frozenset({"ratio"}), 0.0, 1.0),
    PropertyDefinition("temporal_persistence", frozenset({"ratio"}), 0.0, 1.0),
    PropertyDefinition("accel_x", frozenset({"g", "m/s2"}), -1000.0, 1000.0, requires_reference=True, requires_orientation=True, allowed_axes=frozenset({"x"})),
    PropertyDefinition("accel_y", frozenset({"g", "m/s2"}), -1000.0, 1000.0, requires_reference=True, requires_orientation=True, allowed_axes=frozenset({"y"})),
    PropertyDefinition("accel_z", frozenset({"g", "m/s2"}), -1000.0, 1000.0, requires_reference=True, requires_orientation=True, allowed_axes=frozenset({"z"})),
    PropertyDefinition("water_level_m", frozenset({"m"}), -1000.0, 10000.0, requires_reference=True, requires_orientation=True),
    PropertyDefinition("rate_of_rise_m_per_h", frozenset({"m/h"}), -1000.0, 1000.0, MeasurementStatistic.RATE, requires_reference=True, requires_orientation=True),
    PropertyDefinition("rainfall_mm_h", frozenset({"mm/h"}), 0.0, 10000.0, MeasurementStatistic.RATE),
    PropertyDefinition("soil_moisture_fraction", frozenset({"ratio"}), 0.0, 1.0),
    PropertyDefinition("tilt_rate_deg_h", frozenset({"deg/h"}), -10000.0, 10000.0, MeasurementStatistic.RATE, requires_reference=True, requires_orientation=True),
    PropertyDefinition("vibration_rms", frozenset({"g", "m/s2"}), 0.0, 1000.0, MeasurementStatistic.RMS, requires_reference=True),
    PropertyDefinition("flood_susceptibility", frozenset({"ratio"}), 0.0, 1.0),
    PropertyDefinition("landslide_susceptibility", frozenset({"ratio"}), 0.0, 1.0),
    PropertyDefinition("seismic_context_score", frozenset({"ratio"}), 0.0, 1.0),
    PropertyDefinition("camera_luminance", frozenset({"level"}), 0.0, 255.0),
    PropertyDefinition("camera_blur_score", frozenset({"score", "ratio"}), 0.0, 1.0),
    PropertyDefinition("camera_occlusion_fraction", frozenset({"ratio"}), 0.0, 1.0),
    PropertyDefinition("camera_frame_change", frozenset({"ratio"}), 0.0, 1.0),
)


class MeasurementRegistry:
    """Versioned observed-property and unit contract used before hazard logic."""

    schema_version = "2.0.0"

    def __init__(self, definitions: Iterable[PropertyDefinition] = _DEFAULTS) -> None:
        self._definitions = {item.property_id: item for item in definitions}
        if len(self._definitions) != len(tuple(definitions)):
            raise ValueError("property definitions must be unique")

    def definition(self, property_id: str) -> PropertyDefinition | None:
        return self._definitions.get(property_id)

    def validate(self, observation: Observation) -> MeasurementContractReport:
        reasons: list[str] = []
        invalid: list[str] = []
        suspect: list[str] = []
        usable: list[str] = []
        references: dict[str, str] = {}
        seen: set[str] = set()
        fusion_allowed = True

        for measurement in observation.measurements:
            key = measurement.source_value_key
            if key in seen:
                invalid.append(key)
                reasons.append(f"duplicate_property:{key}")
                continue
            seen.add(key)
            definition = self.definition(measurement.observed_property_id)
            if definition is None:
                invalid.append(key)
                reasons.append(f"unknown_property:{key}")
                continue
            if measurement.unit not in definition.allowed_units:
                invalid.append(key)
                reasons.append(f"unit_not_admissible:{key}:{measurement.unit}")
                continue
            if definition.minimum is not None and measurement.value < definition.minimum:
                invalid.append(key)
                reasons.append(f"below_property_range:{key}")
                continue
            if definition.maximum is not None and measurement.value > definition.maximum:
                invalid.append(key)
                reasons.append(f"above_property_range:{key}")
                continue
            if definition.statistic is not None and measurement.statistic is not definition.statistic:
                invalid.append(key)
                reasons.append(f"statistic_mismatch:{key}")
                continue
            if definition.allowed_axes and measurement.axis not in definition.allowed_axes:
                invalid.append(key)
                reasons.append(f"axis_mismatch:{key}")
                continue
            if definition.requires_orientation and not measurement.orientation:
                invalid.append(key)
                reasons.append(f"orientation_missing:{key}")
                continue
            if definition.requires_reference:
                if not measurement.reference:
                    invalid.append(key)
                    reasons.append(f"reference_missing:{key}")
                    continue
                references[key] = measurement.reference
                if "unqualified" in measurement.reference:
                    fusion_allowed = False
                    reasons.append(f"reference_unqualified:{key}")
            if measurement.quality in {MeasurementQuality.INVALID, MeasurementQuality.MISSING}:
                invalid.append(key)
                reasons.append(f"quality_not_usable:{key}:{measurement.quality.value}")
                continue
            if measurement.quality is MeasurementQuality.SUSPECT:
                suspect.append(key)
                reasons.append(f"quality_suspect:{key}")
            usable.append(key)
            if measurement.uncertainty is None:
                reasons.append(f"uncertainty_unknown:{key}")

        if set(observation.values) != seen:
            reasons.append("measurement_cardinality_mismatch")
            invalid.extend(sorted(set(observation.values) - seen))

        # Measurements carrying the same semantic family but incompatible references cannot be fused.
        reference_families = {
            "motion": [references[k] for k in references if k.startswith("accel_") or "tilt" in k or "vibration" in k],
            "vertical": [references[k] for k in references if "water_level" in k or "elevation" in k or "depth" in k],
        }
        for family, values in reference_families.items():
            if len(set(values)) > 1:
                fusion_allowed = False
                reasons.append(f"reference_incompatible:{family}")

        structural_prefixes = (
            "duplicate_property:", "unknown_property:", "unit_not_admissible:",
            "below_property_range:", "above_property_range:", "statistic_mismatch:",
            "axis_mismatch:", "orientation_missing:", "reference_missing:", "measurement_cardinality_mismatch",
        )
        valid = not any(code.startswith(structural_prefixes) for code in reasons)
        if valid:
            reasons.append("measurement_contract_valid")
        return MeasurementContractReport(
            valid=valid,
            usable_properties=tuple(sorted(set(usable))),
            invalid_properties=tuple(sorted(set(invalid))),
            suspect_properties=tuple(sorted(set(suspect))),
            fusion_allowed=fusion_allowed,
            reason_codes=tuple(sorted(set(reasons))),
        )

    def sanitize(self, observation: Observation) -> tuple[Observation, MeasurementContractReport]:
        report = self.validate(observation)
        if not report.valid:
            raise ValueError("invalid measurement contract: " + ",".join(report.reason_codes))
        usable = set(report.usable_properties)
        values = {k: v for k, v in observation.values.items() if k in usable}
        units = {k: v for k, v in observation.units.items() if k in usable}
        measurements = tuple(m for m in observation.measurements if m.source_value_key in usable)
        flags = tuple(sorted(set(observation.quality_flags + tuple(f"measurement:{code}" for code in report.reason_codes))))
        return observation.model_copy(update={"values": values, "units": units, "measurements": measurements, "quality_flags": flags}), report


def compare_references(left: MeasurementValue, right: MeasurementValue) -> tuple[bool, str]:
    if left.reference is None or right.reference is None:
        return False, "reference_missing"
    if left.reference != right.reference:
        return False, "reference_incompatible"
    if "unqualified" in left.reference:
        return False, "reference_unqualified"
    return True, "reference_compatible"
