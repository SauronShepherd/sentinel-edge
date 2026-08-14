from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5

from sentinel_edge.domain.models import AnalysisResult, HazardKind, IncidentState, Observation
from sentinel_edge.hazards import EarthquakeAdapter, FloodAdapter, LandslideAdapter, WildfireAdapter
from sentinel_edge.semantics import MeasurementRegistry


class AnalysisEnrichmentEngine:
    """Component 2: deterministic feature extraction and bounded hazard analysis."""

    component_id = "component-2-analysis"

    def __init__(self, measurement_registry: MeasurementRegistry | None = None) -> None:
        self.measurements = measurement_registry or MeasurementRegistry()
        self._adapters = {
            HazardKind.WILDFIRE: WildfireAdapter(),
            HazardKind.FLOOD: FloodAdapter(),
            HazardKind.EARTHQUAKE: EarthquakeAdapter(),
            HazardKind.LANDSLIDE: LandslideAdapter(),
        }

    def analyze(self, observation: Observation) -> AnalysisResult:
        sanitized, measurement_report = self.measurements.sanitize(observation)
        result = self._adapters[sanitized.hazard].analyze(sanitized)
        measurement_reasons = tuple(
            code for code in measurement_report.reason_codes
            if code.startswith(("quality_", "uncertainty_", "reference_"))
        )
        result = result.model_copy(update={"reason_codes": tuple(sorted(set(result.reason_codes + measurement_reasons)))})
        if sanitized.capture_age_ms > 5_000:
            result = result.model_copy(update={
                "score": 0.0,
                "state_hint": IncidentState.NORMAL,
                "reason_codes": tuple(sorted(set(result.reason_codes + ("source_ttl_expired_zero_contribution",)))),
            })
        analysis_id = uuid5(
            NAMESPACE_URL,
            f"sentinel-analysis:{observation.observation_id}:{result.model_profile_id}",
        )
        return result.model_copy(
            update={
                "analysis_id": analysis_id,
                "correlation_id": observation.correlation_id,
                "boot_id": observation.boot_id,
                "source_mode": observation.source_mode,
                "source_lineage": observation.source_lineage,
                "produced_at": observation.received_at,
                "event_time": observation.observed_at,
            }
        )

    @property
    def adapter_ids(self) -> tuple[str, ...]:
        return tuple(adapter.adapter_id for adapter in self._adapters.values())
