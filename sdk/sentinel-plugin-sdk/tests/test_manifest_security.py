import pytest
from sentinel_plugin_sdk import Manifest, PermissionSet, Lifecycle, PluginState

def manifest(**kw):
    base = dict(name="safe", version="1", api_version="1", digest="sha256:"+"a"*64,
                permissions=PermissionSet(), modes=frozenset({"analysis"}), contracts=frozenset({"collector.v1"}), max_memory_mb=32, max_cpu_ms=100)
    base.update(kw); return Manifest(**base)

def test_bounds_and_authority():
    assert manifest().name == "safe"
    with pytest.raises(ValueError): manifest(max_memory_mb=0)
    with pytest.raises(ValueError): PermissionSet(filesystem=frozenset({"incident-repository"}))

def test_lifecycle_rejects_illegal_transition():
    lifecycle = Lifecycle(); lifecycle.transition(PluginState.VERIFIED)
    with pytest.raises(ValueError): lifecycle.transition(PluginState.ACTIVE)
