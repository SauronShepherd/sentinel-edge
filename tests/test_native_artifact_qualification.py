import pytest

from sentinel_edge.runtime.native_artifact_qualification import NativeArtifactQualification


def test_signed_native_artifact_requires_all_activation_evidence() -> None:
    receipt = NativeArtifactQualification("sha256:artifact", "sig:1", "abi", "compiler", "hardening", "sandbox", "attack")
    assert receipt.activation_allowed() is True
    assert receipt.as_receipt()["activation_allowed"] is True


def test_missing_native_artifact_evidence_fails_closed() -> None:
    with pytest.raises(ValueError, match="complete qualification"):
        NativeArtifactQualification("sha256:artifact", "sig:1", "abi", "", "hardening", "sandbox", "attack")
