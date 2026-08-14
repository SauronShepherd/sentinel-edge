import pytest
from sentinel_edge.release import build_trust_report

def test_trust_report_distinguishes_hash_only_integrity_from_signed_authenticity() -> None:
    hashed = build_trust_report(digest_verified=True, signature_verified=False)
    signed = build_trust_report(digest_verified=True, signature_verified=True, signer_key_id="release-key")
    assert hashed["trust_level"] == "hash_only_integrity"
    assert hashed["signer_policy"]
    assert signed["trust_level"] == "signed_authenticity"
    assert signed["signer_key_id"] == "release-key"
    assert hashed["private_key_required_for_verification"] is False

def test_trust_report_rejects_signature_without_signer_identity() -> None:
    with pytest.raises(ValueError, match="signer key identifier"):
        build_trust_report(digest_verified=True, signature_verified=True)
