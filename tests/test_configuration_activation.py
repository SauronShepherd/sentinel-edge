from copy import deepcopy
from pathlib import Path

import pytest

from sentinel_edge.configuration import load_configuration_bundle
from sentinel_edge.domain.models import ConfigurationState
from sentinel_edge.scenario import DeterministicScenarioEngine, default_configuration_bundle


def payload(version: str) -> dict:
    raw = default_configuration_bundle().model_dump(mode="json")
    raw["version"] = version
    raw["actor"] = "test-operator"
    return raw


def test_configuration_load_stage_activate_and_last_known_good(tmp_path: Path) -> None:
    loaded = load_configuration_bundle("fixtures/configuration/default-v0.6.0.yaml")
    assert loaded.bundle_id == "sentinel-default"
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    record = engine.activate_configuration(payload("0.4.1"))
    assert record.state is ConfigurationState.ACTIVE
    state = engine.configuration.state()
    assert state["active"]["version"] == "0.4.1"
    assert state["last_known_good"]["version"] == "0.21.0"
    assert {item.workload_id for item in engine.runtime.registry} == {
        "earthquake-trigger",
        "wildfire-stage2",
        "flood-evaluate",
        "landslide-evaluate",
    }
    assert default_configuration_bundle().settings["live_connectors_enabled"] is False


def test_invalid_bundle_never_activates_and_canary_failure_rolls_back(tmp_path: Path) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    good = engine.activate_configuration(payload("0.4.1"))
    assert good.state is ConfigurationState.ACTIVE

    invalid = payload("0.4.2")
    invalid["workloads"] = [item for item in invalid["workloads"] if item["hazard"] != "earthquake"]
    rejected = engine.activate_configuration(invalid)
    assert rejected.state is ConfigurationState.REJECTED
    assert engine.configuration.store.active().version == "0.4.1"

    candidate = payload("0.4.3")
    rolled_back = engine.activate_configuration(candidate, fail_canary=True)
    assert rolled_back.state is ConfigurationState.ROLLED_BACK
    state = engine.configuration.state()
    assert state["active"]["version"] == "0.4.1"
    assert state["last_known_good"]["version"] == "0.4.1"
    assert any("canary_failed" in item["reason_codes"] for item in state["history"])


def test_configuration_hashes_are_strict_and_identity_is_immutable(tmp_path: Path) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    bad_hash = payload("0.4.1")
    bad_hash["model_hashes"] = {"wildfire": "not-a-sha256"}
    with pytest.raises(ValueError, match="SHA-256"):
        engine.activate_configuration(bad_hash)

    first = payload("0.4.1")
    engine.activate_configuration(first)
    changed = deepcopy(first)
    changed["settings"]["notification_budget"] = 99
    with pytest.raises(ValueError, match="immutable"):
        engine.activate_configuration(changed)
