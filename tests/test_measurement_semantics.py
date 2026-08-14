from datetime import datetime, timezone

import pytest

from sentinel_edge.analysis import AnalysisEnrichmentEngine
from sentinel_edge.collector import StreamingSourceCollector
from sentinel_edge.domain.models import HazardKind, MeasurementStatistic, Observation, SourceMode
from sentinel_edge.semantics import MeasurementRegistry, compare_references


def _observation(**updates) -> Observation:
    now = datetime(2026, 8, 2, 18, 0, tzinfo=timezone.utc)
    data = {
        "source_id": "flood-gauge-1",
        "hazard": HazardKind.FLOOD,
        "source_mode": SourceMode.FIXTURE,
        "sequence": 1,
        "observed_at": now,
        "received_at": now,
        "values": {"water_level_m": 1.2, "rate_of_rise_m_per_h": 0.3, "rainfall_mm_h": 20.0},
        "units": {"water_level_m": "m", "rate_of_rise_m_per_h": "m/h", "rainfall_mm_h": "mm/h"},
        "measurement_references": {
            "water_level_m": "gauge-datum:station-1",
            "rate_of_rise_m_per_h": "gauge-datum:station-1",
        },
        "measurement_uncertainty": {"water_level_m": 0.02, "rate_of_rise_m_per_h": 0.01},
    }
    data.update(updates)
    return Observation.model_validate(data)


def test_observation_generates_v2_measurement_contract() -> None:
    observation = _observation()
    assert {item.observed_property_id for item in observation.measurements} == set(observation.values)
    rate = next(item for item in observation.measurements if item.observed_property_id == "rainfall_mm_h")
    assert rate.statistic is MeasurementStatistic.RATE
    assert (rate.phenomenon_end - rate.phenomenon_start).total_seconds() == 3600
    report = MeasurementRegistry().validate(observation)
    assert report.valid is True
    assert report.fusion_allowed is True
    assert "measurement_contract_valid" in report.reason_codes


def test_wrong_unit_is_rejected_before_hazard_logic() -> None:
    observation = _observation(units={"water_level_m": "ft", "rate_of_rise_m_per_h": "m/h", "rainfall_mm_h": "mm/h"})
    with pytest.raises(ValueError, match="unit_not_admissible"):
        StreamingSourceCollector().ingest(observation)


def test_invalid_channel_is_removed_and_cannot_hide_in_global_validity() -> None:
    observation = _observation(quality_flags=("invalid:rate_of_rise_m_per_h",))
    result = AnalysisEnrichmentEngine().analyze(observation)
    assert result.abstained is True
    assert result.coverage.value == "partial"
    assert "quality_not_usable:rate_of_rise_m_per_h:invalid" in result.reason_codes


def test_incompatible_references_cannot_be_fused() -> None:
    left = next(item for item in _observation().measurements if item.observed_property_id == "water_level_m")
    right = left.model_copy(update={"reference": "gauge-datum:station-2"})
    compatible, reason = compare_references(left, right)
    assert compatible is False
    assert reason == "reference_incompatible"
