"""Explicitly documented external-authority reference policies."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DocumentedAuthorityEndpoint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    authority: str
    endpoint: str
    documentation_url: str
    allowed: bool = True
    reference_only: bool = True

    def __init__(self, **data):
        super().__init__(**data)
        if not self.authority.strip() or not self.endpoint.startswith("https://") or not self.documentation_url.startswith("https://"):
            raise ValueError("authority, HTTPS endpoint, and documentation URL are required")


class AuthorityResolutionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    authority: str
    endpoint: str
    permitted: bool
    reason: str
    reference_only: bool = True


def resolve_documented_authority(
    endpoint: DocumentedAuthorityEndpoint,
    *,
    requested_endpoint: str,
) -> AuthorityResolutionDecision:
    permitted = endpoint.allowed and requested_endpoint == endpoint.endpoint
    return AuthorityResolutionDecision(
        authority=endpoint.authority, endpoint=requested_endpoint, permitted=permitted,
        reason="documented_endpoint_allowlisted" if permitted else "undocumented_endpoint_rejected",
    )
