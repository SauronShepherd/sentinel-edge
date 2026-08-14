from time import perf_counter_ns

from sentinel_edge.domain.models import AnalysisResult, CoverageState, HazardKind, IncidentState, Observation
from sentinel_edge.qualification.thresholds import decide_with_margin


class WildfireAdapter:
    adapter_id = "wildfire-v2"

    def analyze(self, observation: Observation) -> AnalysisResult:
        started_ns = perf_counter_ns()
        if observation.hazard is not HazardKind.WILDFIRE:
            raise ValueError("wildfire adapter received another hazard")
        smoke = max(0.0, min(1.0, observation.values.get("smoke_score", 0.0)))
        flame = max(0.0, min(1.0, observation.values.get("flame_score", 0.0)))
        persistence = max(0.0, min(1.0, observation.values.get("temporal_persistence", 0.0)))
        luminance = observation.values.get("camera_luminance", 128.0)
        blur_score = observation.values.get("camera_blur_score", 100.0)
        occlusion = max(0.0, min(1.0, observation.values.get("camera_occlusion_fraction", 0.0)))
        frame_change = max(0.0, min(1.0, observation.values.get("camera_frame_change", 1.0)))
        region_smoke = max(0.0, min(1.0, observation.values.get("stage2_region_smoke_score", smoke)))
        region_flame = max(0.0, min(1.0, observation.values.get("stage2_region_flame_score", flame)))
        region_x = max(0.0, min(1.0, observation.values.get("stage2_region_center_x", 0.5)))
        region_y = max(0.0, min(1.0, observation.values.get("stage2_region_center_y", 0.5)))
        camera_sector_index = float(min(8, int(region_y * 3.0) * 3 + int(region_x * 3.0)))
        health_reasons: list[str] = []
        if luminance < 12.0 or "camera_dark" in observation.quality_flags:
            health_reasons.append("camera_dark")
        if blur_score < 20.0 or "camera_blurred" in observation.quality_flags:
            health_reasons.append("camera_blurred")
        if occlusion > 0.85 or "camera_occluded" in observation.quality_flags:
            health_reasons.append("camera_occluded")
        if frame_change <= 0.01 or "camera_frozen" in observation.quality_flags:
            health_reasons.append("camera_frozen")
        score = min(1.0, 0.55 * smoke + 0.30 * flame + 0.15 * persistence)
        # Stage-1 is intentionally small and deterministic.  The uncertainty
        # signal is explicit so consumers cannot mistake a score for certainty;
        # latency is measured around the complete local stage.
        uncertainty = min(1.0, 0.60 * (1.0 - persistence) + 0.40 * (1.0 - max(smoke, flame)))
        stage2_score = round(min(1.0, 0.65 * region_smoke + 0.35 * region_flame), 6)
        if len(health_reasons) >= 2 or "camera_frozen" in health_reasons:
            coverage = CoverageState.BLIND
        elif health_reasons:
            coverage = CoverageState.PARTIAL
        else:
            coverage = CoverageState.SUFFICIENT
        # A single positive frame must never become a verified/confirmed
        # visible-smoke decision. Persistence is an explicit independent
        # guard, not just another weighted score feature.
        persistence_sufficient = persistence >= 0.50
        threshold_decision = decide_with_margin(
            score,
            thresholds=((0.30, IncidentState.WATCH), (0.55, IncidentState.SUSPECTED), (0.80, IncidentState.CONFIRMED)),
        )
        state = threshold_decision.state
        abstained = coverage is not CoverageState.SUFFICIENT or threshold_decision.abstained
        if not persistence_sufficient and state in {IncidentState.SUSPECTED, IncidentState.CONFIRMED}:
            state = IncidentState.WATCH
            abstained = True
        if abstained and state.value not in {IncidentState.NORMAL.value, IncidentState.WATCH.value}:
            state = IncidentState.WATCH
        reasons_list = health_reasons + ["camera_sector_only"] + (["visual_quality_abstention"] if abstained else [])
        if not persistence_sufficient:
            reasons_list.append("temporal_persistence_insufficient")
        if threshold_decision.reason_code:
            reasons_list.append(threshold_decision.reason_code)
        reasons = tuple(sorted(set(reasons_list)))
        latency_ms = (perf_counter_ns() - started_ns) / 1_000_000.0
        return AnalysisResult(
            observation_id=observation.observation_id,
            hazard=observation.hazard,
            score=score,
            state_hint=state,
            features={
                "smoke": smoke,
                "flame": flame,
                "persistence": persistence,
                "camera_luminance": luminance,
                "camera_blur_score": blur_score,
                "camera_occlusion_fraction": occlusion,
                "camera_frame_change": frame_change,
                "stage1_score": score,
                "stage1_uncertainty": uncertainty,
                "stage1_latency_ms": latency_ms,
                "stage2_score": stage2_score,
                "stage2_region_center_x": region_x,
                "stage2_region_center_y": region_y,
                "camera_sector_index": camera_sector_index,
                "stage2_latency_ms": latency_ms,
            },
            coverage=coverage,
            abstained=abstained,
            reason_codes=reasons,
            model_profile_id="wildfire-deterministic-v2",
        )
