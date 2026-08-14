from datetime import datetime, timedelta, timezone

from sentinel_edge.domain.models import CoverageState, HazardKind, IncidentState, Observation, SourceMode
from sentinel_edge.hazards import FloodAdapter, FloodThresholdProfile, LandslideAdapter


def observation(hazard: HazardKind, sequence: int, values: dict[str, float], *, when: datetime, source: str) -> Observation:
    return Observation(
        source_id=source,
        hazard=hazard,
        source_mode=SourceMode.FIXTURE,
        sequence=sequence,
        observed_at=when,
        received_at=when,
        values=values,
        units={key: "unit" for key in values},
    )


def test_flood_threshold_profile_is_versioned_and_configurable() -> None:
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
    profile = FloodThresholdProfile(
        profile_id="flood-test-v9",
        threshold_source="site-alpha-calibration",
        threshold_version="9",
        water_level_watch_m=0.1,
        water_level_suspected_m=0.2,
        water_level_confirmed_m=0.3,
        rise_watch_m_per_h=0.01,
        rise_suspected_m_per_h=0.02,
        rise_confirmed_m_per_h=0.03,
    )
    result = FloodAdapter(profile).analyze(observation(
        HazardKind.FLOOD,
        1,
        {"water_level_m": 0.5, "rate_of_rise_m_per_h": 0.05},
        when=now,
        source="river-alpha",
    ))
    assert result.state_hint is IncidentState.CONFIRMED
    assert result.model_profile_id == "flood-test-v9"
    assert "threshold_source:site-alpha-calibration" in result.reason_codes
    assert "threshold_version:9" in result.reason_codes


def test_flood_missingness_is_not_zero_fill_and_susceptibility_is_context_only() -> None:
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
    adapter = FloodAdapter()
    missing = adapter.analyze(observation(
        HazardKind.FLOOD,
        1,
        {"rate_of_rise_m_per_h": 0.6, "flood_susceptibility": 1.0},
        when=now,
        source="river-beta",
    ))
    assert missing.coverage is CoverageState.PARTIAL
    assert missing.abstained is True
    assert missing.state_hint is IncidentState.WATCH
    assert missing.features["missing_water_level_m"] == 1.0
    assert missing.features["flood_susceptibility"] == 1.0

    susceptibility_only = adapter.analyze(observation(
        HazardKind.FLOOD,
        2,
        {"flood_susceptibility": 1.0},
        when=now + timedelta(minutes=1),
        source="river-beta",
    ))
    assert susceptibility_only.coverage is CoverageState.BLIND
    assert susceptibility_only.state_hint is IncidentState.WATCH
    assert susceptibility_only.score == 0.0


def test_flood_optional_forecast_failure_falls_back_to_deterministic_rules() -> None:
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)

    def broken(_observation: Observation) -> float:
        raise RuntimeError("model unavailable")

    result = FloodAdapter(forecast_predictor=broken).analyze(observation(
        HazardKind.FLOOD,
        1,
        {"water_level_m": 1.2, "rate_of_rise_m_per_h": 0.3, "rainfall_mm_h": 25.0},
        when=now,
        source="river-gamma",
    ))
    assert "forecast_failed_deterministic_fallback" in result.reason_codes
    assert result.coverage is CoverageState.SUFFICIENT
    assert result.state_hint in {IncidentState.WATCH, IncidentState.SUSPECTED, IncidentState.CONFIRMED}


def test_landslide_calculates_rainfall_windows_and_keeps_context_separate_from_movement() -> None:
    adapter = LandslideAdapter()
    start = datetime(2026, 8, 2, 0, 0, tzinfo=timezone.utc)
    first = adapter.analyze(observation(
        HazardKind.LANDSLIDE,
        1,
        {"rainfall_mm_h": 10.0, "soil_moisture_fraction": 0.9, "tilt_rate_deg_h": 0.0, "vibration_rms": 0.0},
        when=start,
        source="slope-alpha",
    ))
    second = adapter.analyze(observation(
        HazardKind.LANDSLIDE,
        2,
        {"rainfall_mm_h": 20.0, "soil_moisture_fraction": 0.9, "tilt_rate_deg_h": 0.0, "vibration_rms": 0.0},
        when=start + timedelta(hours=1),
        source="slope-alpha",
    ))
    assert first.features["rainfall_1h_mm"] == 0.0
    assert second.features["rainfall_1h_mm"] == 10.0
    assert second.features["rainfall_6h_mm"] == 10.0
    assert second.features["rainfall_24h_mm"] == 10.0
    assert second.features["susceptibility_score"] > 0.25
    assert second.features["movement_score"] == 0.0
    assert second.state_hint is IncidentState.WATCH
    assert "susceptibility_separate_from_movement" in second.reason_codes


def test_landslide_movement_evidence_and_safe_public_wording() -> None:
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
    adapter = LandslideAdapter()
    result = adapter.analyze(observation(
        HazardKind.LANDSLIDE,
        1,
        {"tilt_rate_deg_h": 1.2, "vibration_rms": 0.5, "soil_moisture_fraction": 0.2},
        when=now,
        source="slope-beta",
    ))
    assert result.state_hint is IncidentState.CONFIRMED
    summary = adapter.public_summary(result).lower()
    assert "imminent" not in summary
    assert "will" not in summary
    assert "human review" in summary


def test_landslide_recommends_faster_cadence_only_for_fresh_context() -> None:
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
    adapter = LandslideAdapter()
    baseline = adapter.analyze(observation(
        HazardKind.LANDSLIDE, 1,
        {"tilt_rate_deg_h": 0.0, "vibration_rms": 0.0, "soil_moisture_fraction": 0.2},
        when=now, source="slope-cadence",
    ))
    contextual = adapter.analyze(observation(
        HazardKind.LANDSLIDE, 2,
        {"tilt_rate_deg_h": 0.0, "vibration_rms": 0.0, "soil_moisture_fraction": 0.2,
         "seismic_context_score": 0.8},
        when=now + timedelta(minutes=1), source="slope-cadence",
    ))
    assert baseline.features["cadence_multiplier_recommended"] == 1.0
    assert contextual.features["cadence_multiplier_recommended"] == 2.0
    assert "seismic_context_elevated" in contextual.reason_codes
