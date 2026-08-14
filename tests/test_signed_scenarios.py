from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest

from sentinel_edge.scenario import sign_scenario, verify_signed_scenario


def test_signed_scenario_verification_binds_manifest_hash() -> None:
    private = Ed25519PrivateKey.generate()
    manifest = {"scenario_id": "signed-v1", "observations": []}
    envelope = sign_scenario(manifest, private)
    verified = verify_signed_scenario(envelope, private.public_key())
    assert verified["manifest"] == manifest
    assert len(verified["manifest_sha256"]) == 64


def test_signed_scenario_rejects_tampering() -> None:
    private = Ed25519PrivateKey.generate()
    envelope = sign_scenario({"scenario_id": "signed-v1", "observations": []}, private)
    envelope["manifest"]["scenario_id"] = "tampered"
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_signed_scenario(envelope, private.public_key())
