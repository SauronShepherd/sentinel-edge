import hashlib
import pytest
from sentinel_plugin_sdk import Lifecycle, PluginState, Manifest, Permissions

def test_signature_digest_and_dependency_surface():
    digest = "sha256:" + "a" * 64
    life = Lifecycle()
    with pytest.raises(ValueError, match="invalid_digest"): life.verify("sha256:" + "z" * 64, "sig:" + "a" * 64)
    with pytest.raises(ValueError, match="invalid_signature"): life.verify(digest, "x")
    sig = "sig:" + hashlib.sha256(digest.encode()).hexdigest()
    life.verify(digest, sig); life.compatibility({"1"}, "1"); life.self_test(True)
    assert life.state == PluginState.SELF_TESTED
    with pytest.raises(ValueError): Permissions(network=frozenset({"*"}))
