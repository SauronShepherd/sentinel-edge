from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from sentinel_edge.release.independent_build import build_attestation, verify_attestation


def test_attestation_signature_does_not_override_builder_policy() -> None:
    key = Ed25519PrivateKey.generate()
    attestation = build_attestation(builder_id="builder-a", host_fingerprint="host-a", environment_digest="env-a", source_digest="src", artifact_digest="artifact", private_key=key)
    assert verify_attestation(attestation, key.public_key(), expected_builder_id="builder-a") == []
    assert "build_attestation_builder_policy_mismatch" in verify_attestation(attestation, key.public_key(), expected_builder_id="builder-b")


def test_attestation_policy_version_is_authoritative() -> None:
    key = Ed25519PrivateKey.generate()
    attestation = build_attestation(builder_id="builder-a", host_fingerprint="host-a", environment_digest="env-a", source_digest="src", artifact_digest="artifact", private_key=key)
    assert "build_attestation_policy_mismatch" in verify_attestation(attestation, key.public_key(), expected_policy_version="attestation-policy-v2")
