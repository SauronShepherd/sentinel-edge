"""Fail-closed admission gate for direct-upload session creation."""

from __future__ import annotations

from dataclasses import dataclass

from sentinel_edge.qualification.upload_grants import UploadGrant, UploadGrantAuthority


@dataclass(frozen=True)
class UploadAdmission:
    authenticated: bool
    authorized: bool
    quota_available: bool
    consent_valid: bool
    source_policy_allowed: bool

    @property
    def allowed(self) -> bool:
        return all((self.authenticated, self.authorized, self.quota_available, self.consent_valid, self.source_policy_allowed))


def create_upload_session(*, authority: UploadGrantAuthority, principal_id: str, scope: str,
                          expires_at, max_bytes: int, admission: UploadAdmission) -> UploadGrant | None:
    """Issue no grant unless every Component-5 admission control passes."""
    if not admission.allowed:
        return None
    return authority.issue(principal_id=principal_id, scope=scope, expires_at=expires_at, max_bytes=max_bytes)
