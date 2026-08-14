import pytest

from sentinel_edge.privacy.local_evidence_protection import LocalEvidenceProtection


def test_copied_evidence_volume_alone_cannot_recover_protected_bytes() -> None:
    protection = LocalEvidenceProtection("deploy-1", True, "application-authenticated", "key-vault-1", "evidence-volume-1")
    assert protection.copied_volume_access(supplied_key_authority=None) is False
    assert protection.copied_volume_access(supplied_key_authority="other-key-vault") is False
    assert protection.copied_volume_access(supplied_key_authority="key-vault-1") is True


def test_key_authority_cannot_be_the_evidence_volume() -> None:
    with pytest.raises(ValueError, match="separate"):
        LocalEvidenceProtection("deploy-1", True, "full-disk", "volume", "volume")
