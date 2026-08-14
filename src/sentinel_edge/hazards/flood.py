from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from sentinel_edge.domain.models import AnalysisResult, CoverageState, HazardKind, IncidentState, Observation
from sentinel_edge.hazards.forecast import ForecastMetadata


@dataclass(frozen=True)
class FloodThresholdProfile:
    """Versioned site thresholds. Susceptibility is context and never observation truth."""

    profile_id: str = "flood-rules-v2"
    threshold_source: str = "bundled-development-profile"
    threshold_version: str = "2026-08-02"
    water_level_watch_m: float = 0.50
    water_level_suspected_m: float = 1.00
    water_level_confirmed_m: float = 1.80
    rise_watch_m_per_h: float = 0.10
    rise_suspected_m_per_h: float = 0.25
    rise_confirmed_m_per_h: float = 0.45
    rainfall_watch_mm_h: float = 10.0
    rainfall_suspected_mm_h: float = 30.0
    rainfall_confirmed_mm_h: float = 50.0

    def __post_init__(self) -> None:
        groups = (
            (self.water_level_watch_m, self.water_level_suspected_m, self.water_level_confirmed_m),
            (self.rise_watch_m_per_h, self.rise_suspected_m_per_h, self.rise_confirmed_m_per_h),
            (self.rainfall_watch_mm_h, self.rainfall_suspected_mm_h, self.rainfall_confirmed_mm_h),
        )
        if any(not (0 <= watch < suspected < confirmed) for watch, suspected, confirmed in groups):
            raise ValueError("flood thresholds must be non-negative and strictly ordered")
        if not self.profile_id.strip() or not self.threshold_source.strip() or not self.threshold_version.strip():
            raise ValueError("flood threshold provenance must be non-blank")


class FloodAdapter:
    adapter_id = "flood-v2"

    def __init__(
        self,
        profile: FloodThresholdProfile | None = None,
        *,
        forecast_predictor: Callable[[Observation], float | ForecastMetadata] | None = None,
        forecast_horizon_seconds: int = 3600,
        forecast_uncertainty: float = 0.25,
        forecast_profile_id: str = "flood-forecast-development-v1",
    ) -> None:
        self.profile = profile or FloodThresholdProfile()
        self._forecast_predictor = forecast_predictor
        self._forecast_horizon_seconds = forecast_horizon_seconds
        self._forecast_uncertainty = forecast_uncertainty
        self._forecast_profile_id = forecast_profile_id

    @staticmethod
    def _channel_score(value: float, watch: float, suspected: float, confirmed: float) -> float:
        if value < watch:
            return 0.0
        if value < suspected:
            return 0.25 + 0.29 * ((value - watch) / (suspected - watch))
        if value < confirmed:
            return 0.55 + 0.29 * ((value - suspected) / (confirmed - suspected))
        return min(1.0, 0.85 + 0.15 * ((value - confirmed) / max(confirmed, 1e-9)))

    def analyze(self, observation: Observation) -> AnalysisResult:
        if observation.hazard is not HazardKind.FLOOD:
            raise ValueError("flood adapter received another hazard")

        required = {"water_level_m", "rate_of_rise_m_per_h"}
        present = set(observation.values)
        missing = required - present
        p = self.profile

        features: dict[str, float] = {
            "water_level_present": float("water_level_m" in present),
            "rate_of_rise_present": float("rate_of_rise_m_per_h" in present),
            "rainfall_present": float("rainfall_mm_h" in present),
            "susceptibility_present": float("flood_susceptibility" in present),
            "flood_susceptibility": max(0.0, min(1.0, observation.values.get("flood_susceptibility", 0.0))),
        }
        channel_scores: list[tuple[float, float]] = []
        if "water_level_m" in present:
            value = max(0.0, observation.values["water_level_m"])
            features["water_level_m"] = value
            channel_scores.append((0.50, self._channel_score(
                value, p.water_level_watch_m, p.water_level_suspected_m, p.water_level_confirmed_m
            )))
        if "rate_of_rise_m_per_h" in present:
            value = max(0.0, observation.values["rate_of_rise_m_per_h"])
            features["rise_m_h"] = value
            channel_scores.append((0.35, self._channel_score(
                value, p.rise_watch_m_per_h, p.rise_suspected_m_per_h, p.rise_confirmed_m_per_h
            )))
        if "rainfall_mm_h" in present:
            value = max(0.0, observation.values["rainfall_mm_h"])
            features["rain_mm_h"] = value
            channel_scores.append((0.15, self._channel_score(
                value, p.rainfall_watch_mm_h, p.rainfall_suspected_mm_h, p.rainfall_confirmed_mm_h
            )))

        # Missing channels are not silently zero-filled. The observed weights are renormalized,
        # then a required-channel cap and abstention prevent incomplete evidence from strengthening state.
        total_weight = sum(weight for weight, _ in channel_scores)
        deterministic_score = (
            sum(weight * score for weight, score in channel_scores) / total_weight if total_weight else 0.0
        )
        reasons = [
            f"threshold_source:{p.threshold_source}",
            f"threshold_version:{p.threshold_version}",
            "susceptibility_separate_from_observation",
            "deterministic_rules",
        ]

        forecast = ForecastMetadata.unavailable()
        if self._forecast_predictor is not None:
            try:
                raw_forecast = self._forecast_predictor(observation)
                forecast = raw_forecast if isinstance(raw_forecast, ForecastMetadata) else ForecastMetadata.from_prediction(
                    float(raw_forecast), horizon_seconds=self._forecast_horizon_seconds,
                    uncertainty=self._forecast_uncertainty, profile_id=self._forecast_profile_id,
                )
                features.update(forecast.feature_values())
                reasons.append(forecast.reason_code)
                # Forecast may corroborate but cannot replace direct observations.
                assert forecast.score is not None
                deterministic_score = min(1.0, 0.85 * deterministic_score + 0.15 * forecast.score)
            except Exception:  # deterministic fallback must survive any optional-model failure
                forecast = ForecastMetadata.unavailable("forecast_failed_deterministic_fallback")
                reasons.append("forecast_failed_deterministic_fallback")
        else:
            reasons.append(forecast.reason_code)
        features.update(forecast.feature_values())

        if len(missing) == len(required):
            coverage = CoverageState.BLIND
            abstained = True
            score = 0.0
            state = IncidentState.WATCH
            reasons.extend(("required_channels_missing", "missing_data_mask_applied"))
        elif missing:
            coverage = CoverageState.PARTIAL
            abstained = True
            score = min(deterministic_score, 0.54)
            state = IncidentState.WATCH if score >= 0.25 else IncidentState.NORMAL
            reasons.extend(("required_channel_missing", "missing_data_mask_applied"))
        else:
            coverage = CoverageState.SUFFICIENT
            abstained = False
            score = deterministic_score
            state = (
                IncidentState.CONFIRMED if score >= 0.85
                else IncidentState.SUSPECTED if score >= 0.55
                else IncidentState.WATCH if score >= 0.25
                else IncidentState.NORMAL
            )

        for key in sorted(missing):
            features[f"missing_{key}"] = 1.0

        return AnalysisResult(
            observation_id=observation.observation_id,
            hazard=observation.hazard,
            score=score,
            state_hint=state,
            features=features,
            coverage=coverage,
            abstained=abstained,
            reason_codes=tuple(sorted(set(reasons))),
            model_profile_id=p.profile_id,
        )
