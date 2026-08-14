import pytest

from sentinel_edge.qualification.energy_window import CompleteNodeEnergyWindow


def test_complete_node_energy_includes_camera_storage_cooling_and_idle() -> None:
    report = CompleteNodeEnergyWindow("scenario-1", 10.0, 20.0, {"camera": 2.0, "storage": 1.0, "cooling": 3.0, "idle": 4.0})
    assert report.duration_seconds == 10.0
    assert report.total_watt_seconds == 10.0


def test_missing_component_fails_when_instrumentation_permits() -> None:
    with pytest.raises(ValueError, match="complete-node"):
        CompleteNodeEnergyWindow("scenario-1", 0.0, 1.0, {"camera": 1.0})
