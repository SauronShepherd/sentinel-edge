import pytest

from sentinel_edge.operations import (
    PluginCapability,
    PluginLifecycle,
    PluginManifest,
    validate_plugin_graph,
    validate_plugin_transition,
)


def test_plugin_capabilities_are_typed_and_allowlisted() -> None:
    manifest = PluginManifest(plugin_id="wildfire", capabilities=(PluginCapability.ANALYZE,))
    assert manifest.capabilities == (PluginCapability.ANALYZE,)
    with pytest.raises(ValueError):
        PluginManifest.model_validate({"plugin_id": "wildfire", "capabilities": ["arbitrary_authority"]})


def test_non_incident_plugin_cannot_claim_incident_lifecycle_authority() -> None:
    with pytest.raises(ValueError, match="reserved"):
        PluginManifest(plugin_id="wildfire", capabilities=(PluginCapability.INCIDENT_LIFECYCLE,))
    assert PluginManifest(plugin_id="incident", capabilities=(PluginCapability.INCIDENT_LIFECYCLE,))


def test_plugin_graph_rejects_cycles_and_illegal_lifecycle_transitions() -> None:
    left = PluginManifest(plugin_id="left", dependencies=("right",))
    right = PluginManifest(plugin_id="right", dependencies=("left",))
    with pytest.raises(ValueError, match="cycle"):
        validate_plugin_graph((left, right))
    assert validate_plugin_transition(PluginLifecycle.DECLARED, PluginLifecycle.READY) is PluginLifecycle.READY
    with pytest.raises(ValueError, match="illegal"):
        validate_plugin_transition(PluginLifecycle.STOPPED, PluginLifecycle.RUNNING)
