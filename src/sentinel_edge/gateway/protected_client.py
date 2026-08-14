"""Admission policy for restricted offline evidence clients."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProtectedClientDecision:
    allowed: bool
    reason: str


def authorize_restricted_offline_evidence(*, profile_id: str, native_client: bool,
                                          authenticated: bool, protected_storage: bool) -> ProtectedClientDecision:
    if profile_id != "protected-native-client-v1":
        return ProtectedClientDecision(False, "declared_protected_profile_required")
    if not native_client:
        return ProtectedClientDecision(False, "native_client_required")
    if not authenticated:
        return ProtectedClientDecision(False, "authenticated_client_required")
    if not protected_storage:
        return ProtectedClientDecision(False, "protected_storage_required")
    return ProtectedClientDecision(True, "protected_native_client_admitted")
