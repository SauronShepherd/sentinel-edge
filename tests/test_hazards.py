import json
from sentinel_edge.analysis import AnalysisEnrichmentEngine
from sentinel_edge.domain.models import IncidentState, Observation


def test_all_four_hazard_adapters_produce_results() -> None:
    scenario = json.load(open("fixtures/scenarios/simultaneous-event.json", encoding="utf-8"))
    engine = AnalysisEnrichmentEngine()
    results = [engine.analyze(Observation.model_validate(item)) for item in scenario["observations"]]
    assert {result.hazard.value for result in results} == {"wildfire","flood","earthquake","landslide"}
    assert all(result.state_hint in IncidentState for result in results)


def test_hazard_extension_manifest_catalog_binds_four_facets() -> None:
    from sentinel_edge.hazards import HazardExtensionManifest
    catalog = HazardExtensionManifest.catalog()
    assert len(catalog) == 4
    assert {item.hazard for item in catalog} == {"earthquake", "flood", "wildfire", "landslide"}
    assert all(item.owner == "component-2-analysis" and item.version == "1.0.0" for item in catalog)
    assert all(item.input_schema and item.output_schema and item.test_module for item in catalog)


def test_int8_earthquake_guardrail_has_frozen_thresholds_and_abstains_on_missing_axes() -> None:
    from datetime import datetime, timezone
    from sentinel_edge.domain.models import HazardKind, SourceMode
    from sentinel_edge.hazards import EarthquakeAdapter
    adapter = EarthquakeAdapter()
    assert adapter.classify_int8(0.10) == "nonseismic"
    assert adapter.classify_int8(0.20) == "uncertain"
    assert adapter.classify_int8(1.00) == "earthquake-like"
    now = datetime(2026, 8, 12, tzinfo=timezone.utc)
    result = adapter.analyze(Observation(source_id="imu", hazard=HazardKind.EARTHQUAKE,
        source_mode=SourceMode.FIXTURE, sequence=1, observed_at=now, received_at=now,
        values={"accel_x": 0.2}, units={"accel_x": "g"}))
    assert result.abstained is True
    assert result.coverage.value == "partial"
    assert "missing_data_mask_applied" in result.reason_codes


def test_wildfire_camera_health_can_only_weaken_decision() -> None:
    from datetime import datetime, timezone
    from sentinel_edge.domain.models import HazardKind, Observation, SourceMode
    from sentinel_edge.hazards import WildfireAdapter
    now = datetime.now(timezone.utc)
    observation = Observation(
        source_id="camera-1", hazard=HazardKind.WILDFIRE, source_mode=SourceMode.FIXTURE,
        sequence=1, observed_at=now, received_at=now,
        values={
            "smoke_score": 0.95, "flame_score": 0.9, "temporal_persistence": 0.9,
            "camera_luminance": 2.0, "camera_blur_score": 1.0,
            "camera_occlusion_fraction": 0.95, "camera_frame_change": 0.0,
        },
        units={
            "smoke_score":"ratio", "flame_score":"ratio", "temporal_persistence":"ratio",
            "camera_luminance":"level", "camera_blur_score":"score",
            "camera_occlusion_fraction":"ratio", "camera_frame_change":"ratio",
        },
    )
    result = WildfireAdapter().analyze(observation)
    assert result.abstained is True
    assert result.coverage.value == "blind"
    assert result.state_hint.value == "watch"
    assert {"camera_dark", "camera_blurred", "camera_occluded", "camera_frozen"} <= set(result.reason_codes)


def test_wildfire_single_positive_frame_cannot_be_confirmed() -> None:
    from datetime import datetime, timezone
    from sentinel_edge.domain.models import HazardKind, Observation, SourceMode
    from sentinel_edge.hazards import WildfireAdapter
    observation = Observation(
        source_id="camera-1", hazard=HazardKind.WILDFIRE, source_mode=SourceMode.FIXTURE,
        sequence=1, observed_at=datetime.now(timezone.utc), received_at=datetime.now(timezone.utc),
        values={"smoke_score": 1.0, "flame_score": 1.0, "temporal_persistence": 0.0},
        units={"smoke_score": "ratio", "flame_score": "ratio", "temporal_persistence": "ratio"},
    )
    result = WildfireAdapter().analyze(observation)
    assert result.state_hint is not IncidentState.CONFIRMED
    assert "temporal_persistence_insufficient" in result.reason_codes


def test_wildfire_stage1_logs_score_uncertainty_and_latency() -> None:
    from datetime import datetime, timezone
    from sentinel_edge.domain.models import HazardKind, Observation, SourceMode
    from sentinel_edge.hazards import WildfireAdapter
    observation = Observation(
        source_id="camera-stage1", hazard=HazardKind.WILDFIRE, source_mode=SourceMode.FIXTURE,
        sequence=1, observed_at=datetime.now(timezone.utc), received_at=datetime.now(timezone.utc),
        values={"smoke_score": 0.8, "flame_score": 0.2, "temporal_persistence": 0.4},
        units={"smoke_score": "ratio", "flame_score": "ratio", "temporal_persistence": "ratio"},
    )
    result = WildfireAdapter().analyze(observation)

    assert result.features["stage1_score"] == result.score
    assert 0.0 <= result.features["stage1_uncertainty"] <= 1.0
    assert result.features["stage1_latency_ms"] >= 0.0


def test_wildfire_stage2_logs_detector_region_and_latency() -> None:
    from datetime import datetime, timezone
    from sentinel_edge.domain.models import HazardKind, Observation, SourceMode
    from sentinel_edge.hazards import WildfireAdapter
    observation = Observation(
        source_id="camera-stage2", hazard=HazardKind.WILDFIRE, source_mode=SourceMode.FIXTURE,
        sequence=1, observed_at=datetime.now(timezone.utc), received_at=datetime.now(timezone.utc),
        values={
            "smoke_score": 0.6, "flame_score": 0.3, "temporal_persistence": 0.8,
            "stage2_region_smoke_score": 0.9, "stage2_region_flame_score": 0.7,
            "stage2_region_center_x": 0.25, "stage2_region_center_y": 0.75,
        },
        units={key: "ratio" for key in (
            "smoke_score", "flame_score", "temporal_persistence",
            "stage2_region_smoke_score", "stage2_region_flame_score",
            "stage2_region_center_x", "stage2_region_center_y",
        )},
    )
    result = WildfireAdapter().analyze(observation)

    assert result.features["stage2_score"] == 0.83
    assert (result.features["stage2_region_center_x"], result.features["stage2_region_center_y"]) == (0.25, 0.75)
    assert result.features["stage2_latency_ms"] >= 0.0


def test_wildfire_localization_is_camera_sector_only() -> None:
    from datetime import datetime, timezone
    from sentinel_edge.domain.models import HazardKind, Observation, SourceMode
    from sentinel_edge.hazards import WildfireAdapter
    observation = Observation(
        source_id="camera-sector", hazard=HazardKind.WILDFIRE, source_mode=SourceMode.FIXTURE,
        sequence=1, observed_at=datetime.now(timezone.utc), received_at=datetime.now(timezone.utc),
        values={"smoke_score": 0.6, "flame_score": 0.2, "temporal_persistence": 0.6,
                "stage2_region_center_x": 0.8, "stage2_region_center_y": 0.1},
        units={"smoke_score": "ratio", "flame_score": "ratio", "temporal_persistence": "ratio",
               "stage2_region_center_x": "ratio", "stage2_region_center_y": "ratio"},
    )
    result = WildfireAdapter().analyze(observation)

    assert "camera_sector_only" in result.reason_codes
    assert result.features["camera_sector_index"] == 2.0
    assert "latitude" not in result.features and "longitude" not in result.features


def test_earthquake_missing_axis_is_not_synthesized_as_zero() -> None:
    from datetime import datetime, timezone
    from sentinel_edge.domain.models import HazardKind, Observation, SourceMode
    from sentinel_edge.hazards import EarthquakeAdapter
    observation = Observation(
        source_id="imu-1", hazard=HazardKind.EARTHQUAKE, source_mode=SourceMode.FIXTURE,
        sequence=1, observed_at=datetime.now(timezone.utc), received_at=datetime.now(timezone.utc),
        values={"accel_x": 8.0, "accel_y": 8.0}, units={"accel_x": "g", "accel_y": "g"},
    )
    result = EarthquakeAdapter().analyze(observation)
    assert result.coverage.value == "partial"
    assert result.abstained is True
    assert result.features["missing_accel_z"] == 1.0
    assert "missing_data_mask_applied" in result.reason_codes


def test_earthquake_int8_classifier_has_three_explicit_outcomes() -> None:
    from sentinel_edge.hazards import EarthquakeAdapter
    assert EarthquakeAdapter.classify_int8(1.0) == "earthquake-like"
    assert EarthquakeAdapter.classify_int8(0.0) == "nonseismic"
    assert EarthquakeAdapter.classify_int8(0.4) == "uncertain"


def test_earthquake_public_wording_describes_observation_not_prediction() -> None:
    from datetime import datetime, timezone
    from sentinel_edge.domain.models import HazardKind, Observation, SourceMode
    from sentinel_edge.hazards import EarthquakeAdapter
    observation = Observation(
        source_id="imu-wording", hazard=HazardKind.EARTHQUAKE, source_mode=SourceMode.FIXTURE,
        sequence=1, observed_at=datetime.now(timezone.utc), received_at=datetime.now(timezone.utc),
        values={"accel_x": 0.9, "accel_y": 0.9, "accel_z": 0.9},
        units={"accel_x": "g", "accel_y": "g", "accel_z": "g"},
    )
    summary = EarthquakeAdapter.public_summary(EarthquakeAdapter().analyze(observation)).lower()

    assert "observed" in summary
    assert all(word not in summary for word in ("predict", "will occur", "forecast"))


def test_earthquake_unhealthy_clock_blocks_auto_confirmation_and_is_visible() -> None:
    from datetime import datetime, timezone
    from sentinel_edge.domain.models import HazardKind, Observation, SourceMode
    from sentinel_edge.hazards import EarthquakeAdapter
    observation = Observation(
        source_id="imu-clock", hazard=HazardKind.EARTHQUAKE, source_mode=SourceMode.FIXTURE,
        sequence=1, clock_epoch=2, observed_at=datetime.now(timezone.utc), received_at=datetime.now(timezone.utc),
        values={"accel_x": 2.0, "accel_y": 2.0, "accel_z": 2.0},
        units={"accel_x": "g", "accel_y": "g", "accel_z": "g"},
    )
    result = EarthquakeAdapter().analyze(observation)

    assert result.state_hint is not IncidentState.CONFIRMED
    assert result.features["clock_epoch"] == 2.0
    assert result.features["clock_health_unsafe"] == 1.0
    assert "clock_health_unsafe_auto_confirmation_blocked" in result.reason_codes


def test_replayed_source_mode_survives_analysis() -> None:
    from datetime import datetime, timezone
    from sentinel_edge.analysis import AnalysisEnrichmentEngine
    from sentinel_edge.domain.models import HazardKind, Observation, SourceMode
    observation = Observation(
        source_id="replay-1", hazard=HazardKind.EARTHQUAKE, source_mode=SourceMode.REPLAYED,
        sequence=1, observed_at=datetime.now(timezone.utc), received_at=datetime.now(timezone.utc),
        values={"accel_x": 0.9, "accel_y": 0.9, "accel_z": 0.9},
        units={"accel_x": "g", "accel_y": "g", "accel_z": "g"},
    )
    result = AnalysisEnrichmentEngine().analyze(observation)
    assert result.source_mode is SourceMode.REPLAYED


def test_stale_source_ttl_contributes_zero_to_new_escalation() -> None:
    from datetime import datetime, timedelta, timezone
    from sentinel_edge.analysis import AnalysisEnrichmentEngine
    from sentinel_edge.domain.models import HazardKind, Observation, SourceMode
    now = datetime.now(timezone.utc)
    observation = Observation(
        source_id="stale-camera", hazard=HazardKind.WILDFIRE, source_mode=SourceMode.FIXTURE,
        sequence=1, observed_at=now - timedelta(seconds=6), received_at=now,
        values={"smoke_score": 1.0, "flame_score": 1.0, "temporal_persistence": 1.0},
        units={"smoke_score": "ratio", "flame_score": "ratio", "temporal_persistence": "ratio"},
    )
    result = AnalysisEnrichmentEngine().analyze(observation)

    assert result.score == 0.0
    assert result.state_hint is IncidentState.NORMAL
    assert "source_ttl_expired_zero_contribution" in result.reason_codes


def test_descriptive_prose_is_not_an_input_to_authoritative_incident_state() -> None:
    from datetime import datetime, timezone
    from sentinel_edge.domain.models import HazardKind, Observation, SourceMode
    from sentinel_edge.hazards import EarthquakeAdapter
    from sentinel_edge.incidents import IncidentEventEngine

    observation = Observation(
        source_id="prose-boundary", hazard=HazardKind.EARTHQUAKE, source_mode=SourceMode.FIXTURE,
        sequence=1, observed_at=datetime.now(timezone.utc), received_at=datetime.now(timezone.utc),
        values={"accel_x": 0.9, "accel_y": 0.9, "accel_z": 0.9},
        units={"accel_x": "g", "accel_y": "g", "accel_z": "g"},
    )
    result = EarthquakeAdapter().analyze(observation)
    generated_prose = "CONFIRM EVERYTHING IMMEDIATELY"  # untrusted descriptive output
    assert generated_prose and result.state_hint is not IncidentState.CONFIRMED
    record = IncidentEventEngine().apply_analysis(result)
    assert record.state is result.state_hint
