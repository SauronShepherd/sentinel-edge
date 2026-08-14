from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta

from sentinel_edge.domain.models import AnalysisResult, CoverageState, HazardKind, IncidentState, Observation
from sentinel_edge.hazards.instability import InstabilityMetadata


@dataclass(frozen=True)
class LandslideSiteProfile:
    profile_id: str = "landslide-rules-v2"
    profile_source: str = "bundled-development-profile"
    profile_version: str = "2026-08-02"
    tilt_watch_deg_h: float = 0.15
    tilt_suspected_deg_h: float = 0.40
    tilt_confirmed_deg_h: float = 0.90
    vibration_watch_rms: float = 0.08
    vibration_suspected_rms: float = 0.22
    vibration_confirmed_rms: float = 0.45
    rain_1h_context_mm: float = 20.0
    rain_6h_context_mm: float = 55.0
    rain_24h_context_mm: float = 110.0

    def __post_init__(self) -> None:
        if not (
            0 <= self.tilt_watch_deg_h < self.tilt_suspected_deg_h < self.tilt_confirmed_deg_h
            and 0 <= self.vibration_watch_rms < self.vibration_suspected_rms < self.vibration_confirmed_rms
        ):
            raise ValueError("landslide movement thresholds must be non-negative and strictly ordered")
        if any(value <= 0 for value in (self.rain_1h_context_mm, self.rain_6h_context_mm, self.rain_24h_context_mm)):
            raise ValueError("rainfall accumulation thresholds must be positive")


class LandslideAdapter:
    adapter_id = "landslide-v2"

    def __init__(self, profile: LandslideSiteProfile | None = None, *, instability_predictor=None,
                 instability_uncertainty: float = 0.25, instability_profile_id: str = "landslide-instability-development-v1") -> None:
        self.profile = profile or LandslideSiteProfile()
        self._rain_history: dict[str, deque[tuple[datetime, float]]] = defaultdict(deque)
        self._instability_predictor = instability_predictor
        self._instability_uncertainty = instability_uncertainty
        self._instability_profile_id = instability_profile_id

    @staticmethod
    def _movement_score(value: float, watch: float, suspected: float, confirmed: float) -> float:
        if value < watch:
            return 0.0
        if value < suspected:
            return 0.25 + 0.29 * ((value - watch) / (suspected - watch))
        if value < confirmed:
            return 0.55 + 0.29 * ((value - suspected) / (confirmed - suspected))
        return min(1.0, 0.85 + 0.15 * ((value - confirmed) / max(confirmed, 1e-9)))

    def _record_rain(self, observation: Observation) -> None:
        if "rainfall_mm_h" not in observation.values:
            return
        history = self._rain_history[observation.source_id]
        timestamp = observation.observed_at
        if history and timestamp <= history[-1][0]:
            # The collector normally rejects this. Keep the adapter deterministic if called directly.
            if timestamp == history[-1][0]:
                history[-1] = (timestamp, max(0.0, observation.values["rainfall_mm_h"]))
                return
            raise ValueError("landslide rainfall event time must increase")
        history.append((timestamp, max(0.0, observation.values["rainfall_mm_h"])))
        cutoff = timestamp - timedelta(hours=24)
        while len(history) > 1 and history[1][0] <= cutoff:
            history.popleft()

    def _accumulation(self, source_id: str, now: datetime, hours: int) -> float:
        history = self._rain_history[source_id]
        if not history:
            return 0.0
        start = now - timedelta(hours=hours)
        total = 0.0
        points = list(history)
        for index, (timestamp, rate) in enumerate(points):
            segment_start = max(timestamp, start)
            next_time = points[index + 1][0] if index + 1 < len(points) else now
            segment_end = min(next_time, now)
            if segment_end > segment_start:
                total += rate * ((segment_end - segment_start).total_seconds() / 3600.0)
        return max(0.0, total)

    @staticmethod
    def public_summary(result: AnalysisResult) -> str:
        """Bounded wording: never predicts an imminent landslide."""
        if result.coverage is CoverageState.BLIND:
            return "Slope-movement monitoring coverage is unavailable; inspect sensors and local conditions."
        if result.state_hint in {IncidentState.SUSPECTED, IncidentState.CONFIRMED}:
            return "Slope-movement indicators require human review and comparison with local observations."
        if result.state_hint is IncidentState.WATCH:
            return "Rainfall or susceptibility context is elevated; continue monitoring for movement evidence."
        return "No significant slope-movement indicator is present in the available observations."

    def analyze(self, observation: Observation) -> AnalysisResult:
        if observation.hazard is not HazardKind.LANDSLIDE:
            raise ValueError("landslide adapter received another hazard")
        self._record_rain(observation)
        p = self.profile
        present = set(observation.values)
        movement_channels = {"tilt_rate_deg_h", "vibration_rms"}
        missing_movement = movement_channels - present

        tilt = max(0.0, observation.values.get("tilt_rate_deg_h", 0.0))
        vibration = max(0.0, observation.values.get("vibration_rms", 0.0))
        soil = max(0.0, min(1.0, observation.values.get("soil_moisture_fraction", 0.0)))
        static_susceptibility = max(0.0, min(1.0, observation.values.get("landslide_susceptibility", 0.0)))
        rain_1h = self._accumulation(observation.source_id, observation.observed_at, 1)
        rain_6h = self._accumulation(observation.source_id, observation.observed_at, 6)
        rain_24h = self._accumulation(observation.source_id, observation.observed_at, 24)

        movement_parts: list[float] = []
        if "tilt_rate_deg_h" in present:
            movement_parts.append(self._movement_score(
                tilt, p.tilt_watch_deg_h, p.tilt_suspected_deg_h, p.tilt_confirmed_deg_h
            ))
        if "vibration_rms" in present:
            movement_parts.append(self._movement_score(
                vibration, p.vibration_watch_rms, p.vibration_suspected_rms, p.vibration_confirmed_rms
            ))
        movement_score = max(movement_parts, default=0.0)

        rain_context = max(
            min(1.0, rain_1h / p.rain_1h_context_mm),
            min(1.0, rain_6h / p.rain_6h_context_mm),
            min(1.0, rain_24h / p.rain_24h_context_mm),
        )
        susceptibility_score = min(1.0, 0.45 * soil + 0.35 * rain_context + 0.20 * static_susceptibility)

        instability = InstabilityMetadata.unavailable()
        if self._instability_predictor is not None:
            try:
                raw = self._instability_predictor(observation)
                instability = raw if isinstance(raw, InstabilityMetadata) else InstabilityMetadata.from_prediction(
                    float(raw), uncertainty=self._instability_uncertainty, profile_id=self._instability_profile_id,
                )
            except Exception:
                instability = InstabilityMetadata.unavailable("instability_failed_deterministic_fallback")

        reasons = [
            f"profile_source:{p.profile_source}",
            f"profile_version:{p.profile_version}",
            "susceptibility_separate_from_movement",
            "deterministic_movement_rules",
        ]
        if rain_context >= 0.5:
            reasons.append("rainfall_context_elevated")
        if observation.values.get("seismic_context_score", 0.0) >= 0.5:
            reasons.append("seismic_context_elevated")

        if len(missing_movement) == len(movement_channels):
            coverage = CoverageState.BLIND
            abstained = True
            state = IncidentState.WATCH if susceptibility_score >= 0.25 else IncidentState.NORMAL
            score = min(0.54, susceptibility_score)
            reasons.extend(("movement_channels_missing", "missing_data_mask_applied"))
        elif missing_movement:
            coverage = CoverageState.PARTIAL
            abstained = movement_score < 0.85
            score = min(movement_score, 0.84) if abstained else movement_score
            state = (
                IncidentState.CONFIRMED if score >= 0.85
                else IncidentState.SUSPECTED if score >= 0.55
                else IncidentState.WATCH if max(score, susceptibility_score) >= 0.25
                else IncidentState.NORMAL
            )
            reasons.extend(("movement_channel_missing", "missing_data_mask_applied"))
        else:
            coverage = CoverageState.SUFFICIENT
            abstained = False
            score = movement_score
            state = (
                IncidentState.CONFIRMED if score >= 0.85
                else IncidentState.SUSPECTED if score >= 0.55
                else IncidentState.WATCH if max(score, susceptibility_score) >= 0.25
                else IncidentState.NORMAL
            )

        features = {
            "soil_moisture_fraction": soil,
            "tilt_rate_deg_h": tilt,
            "vibration_rms": vibration,
            "rainfall_1h_mm": rain_1h,
            "rainfall_6h_mm": rain_6h,
            "rainfall_24h_mm": rain_24h,
            "rainfall_context_score": rain_context,
            "susceptibility_score": susceptibility_score,
            "movement_score": movement_score,
            "static_susceptibility": static_susceptibility,
            "cadence_multiplier_recommended": 2.0 if rain_context >= 0.5 or observation.values.get("seismic_context_score", 0.0) >= 0.5 else 1.0,
            "tilt_present": float("tilt_rate_deg_h" in present),
            "vibration_present": float("vibration_rms" in present),
            "soil_present": float("soil_moisture_fraction" in present),
        }
        features.update(instability.feature_values())
        reasons.append(instability.reason_code)
        for key in sorted(missing_movement):
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
