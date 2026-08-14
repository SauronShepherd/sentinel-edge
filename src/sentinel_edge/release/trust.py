"""Explicit trust-level reporting for hash and signature verification."""
from __future__ import annotations
from typing import Literal

def build_trust_report(*, digest_verified: bool, signature_verified: bool, signer_key_id: str | None = None, signer_policy: str = "release-signing-key-required") -> dict[str, object]:
    if signature_verified and not signer_key_id:
        raise ValueError("verified signatures require a signer key identifier")
    if signature_verified:
        level: Literal["signed_authenticity", "hash_only_integrity", "unverified"] = "signed_authenticity"
    elif digest_verified:
        level = "hash_only_integrity"
    else:
        level = "unverified"
    return {"schema": "sentinel-edge-trust-report/1.0", "trust_level": level, "digest_verified": digest_verified, "signature_verified": signature_verified, "signer_key_id": signer_key_id, "signer_policy": signer_policy, "private_key_required_for_verification": False}
