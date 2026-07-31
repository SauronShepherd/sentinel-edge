import pytest
from sentinel_plugin_sdk.manifest import Manifest

def test_all_unknown_incident_capabilities_are_rejected():
    for mode in ("incident-writer", "incident_write", "incident-writer-v2", "write-incidents", "INCIDENT_WRITE", "incident.lifecycle.writer", "anything-new"):
        with pytest.raises(ValueError, match="unknown plugin capability"):
            Manifest("x", "1", "1", "sha256:" + "a" * 64, frozenset(), frozenset({mode}), frozenset(), 1, 1)

def test_dependency_cycles_are_rejected():
    def manifest(name, deps):
        return Manifest(name, "1", "1", "sha256:" + "a" * 64, frozenset(), frozenset({"analysis"}), frozenset(), 1, 1, dependencies=frozenset(deps))
    with pytest.raises(ValueError, match="circular"):
        Manifest.validate_dependency_graph([manifest("a", ["b"]), manifest("b", ["a"])])
