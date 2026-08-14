import math

from sentinel_edge.domain.models import AnalysisResult, CoverageState, HazardKind, IncidentState, Observation
from sentinel_edge.qualification.thresholds import decide_with_margin


class EarthquakeAdapter:
    adapter_id = "earthquake-int8-1d-v1"

    @staticmethod
    def classify_int8(dynamic_acceleration_g: float) -> str:
        """Tiny deterministic INT8-style 1D classifier with explicit abstention band."""
        quantized = max(-128, min(127, round(dynamic_acceleration_g * 64)))
        if quantized >= 54:
            return "earthquake-like"
        if quantized <= 12:
            return "nonseismic"
        return "uncertain"

    @staticmethod
    def public_summary(result: AnalysisResult) -> str:
        """Describe observed motion without predicting a future earthquake."""
        if result.coverage is CoverageState.BLIND:
            return "Seismic monitoring coverage is unavailable; inspect the IMU and local conditions."
        if result.state_hint in {IncidentState.SUSPECTED, IncidentState.CONFIRMED}:
            return "Seismic-like motion was observed; review the waveform and local reports."
        if result.state_hint is IncidentState.WATCH:
            return "Elevated motion context was observed; continue monitoring."
        return "No significant seismic-like motion was observed in the available window."

    def analyze(self, observation: Observation) -> AnalysisResult:
        if observation.hazard is not HazardKind.EARTHQUAKE:
            raise ValueError("earthquake adapter received another hazard")
        required = {"accel_x", "accel_y", "accel_z"}
        missing = required - set(observation.values)
        x = observation.values.get("accel_x", 0.0)
        y = observation.values.get("accel_y", 0.0)
        z = observation.values.get("accel_z", 0.0)
        vibration = max(0.0, math.sqrt(x*x + y*y + z*z) - 1.0)
        score = min(1.0, vibration / 0.75)
        classifier_label = self.classify_int8(vibration)
        threshold_decision = decide_with_margin(
            score,
            thresholds=((0.20, IncidentState.WATCH), (0.45, IncidentState.SUSPECTED), (0.85, IncidentState.CONFIRMED)),
        )
        state = threshold_decision.state
        reasons: list[str] = ["deterministic_trigger"]
        clock_unsafe = observation.clock_epoch > 0
        if clock_unsafe:
            score = min(score, 0.54)
            state = IncidentState.WATCH if score >= 0.20 else IncidentState.NORMAL
            reasons.append("clock_health_unsafe_auto_confirmation_blocked")
        if missing:
            # Missing axes are not zero-valued evidence. Preserve the signal
            # gap and cap the result so incomplete IMU input cannot escalate.
            score = min(score, 0.54)
            state = IncidentState.WATCH if score >= 0.20 else IncidentState.NORMAL
            reasons.extend(("imu_axis_missing", "missing_data_mask_applied"))
            coverage = CoverageState.BLIND if len(missing) == len(required) else CoverageState.PARTIAL
            abstained = True
        else:
            coverage = CoverageState.SUFFICIENT
            abstained = threshold_decision.abstained
            if threshold_decision.reason_code:
                reasons.append(threshold_decision.reason_code)
        features = {"dynamic_acceleration_g": vibration, "int8_quantized_acceleration": float(max(-128, min(127, round(vibration * 64)))), "clock_epoch": float(observation.clock_epoch), "clock_health_unsafe": float(clock_unsafe)}
        for key in sorted(missing):
            features[f"missing_{key}"] = 1.0
        return AnalysisResult(observation_id=observation.observation_id, hazard=observation.hazard, score=score,
                              state_hint=state, features=features, coverage=coverage,
                              abstained=abstained, reason_codes=tuple(sorted(set(reasons + [f"classifier:{classifier_label}"]))),
                              model_profile_id="seismic-int8-1d-v1")
