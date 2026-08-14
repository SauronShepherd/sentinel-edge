"""Fail-closed validation for the collaboration configuration profile."""
from __future__ import annotations

from typing import Any


def validate_collaboration_config(raw: dict[str, Any]) -> tuple[str, ...]:
    root = raw.get("collaboration", raw)
    errors: list[str] = []
    mode = root.get("mode", "disabled")
    enabled = bool(root.get("enabled", False))
    sharing = bool(root.get("sharing_enabled", False))
    research = bool(root.get("research_enabled", False))
    if mode not in {"disabled", "fixture", "email_experimental"}:
        errors.append("MODE_UNSUPPORTED")
    if research and not sharing:
        errors.append("RESEARCH_REQUIRES_SHARING")
    privacy = root.get("privacy", {})
    for key in ("exact_coordinates_allowed", "raw_sensor_data_allowed", "raw_media_allowed", "raw_waveforms_allowed"):
        if privacy.get(key, False):
            errors.append(f"PRIVACY_{key.upper()}_FORBIDDEN")
    if not enabled and mode != "disabled":
        errors.append("DISABLED_MODE_MISMATCH")
    if mode == "email_experimental" and enabled:
        outbound = root.get("outbound", {})
        inbound = root.get("inbound", {})
        if not sharing:
            errors.append("EMAIL_REQUIRES_SHARING")
        if not outbound.get("enabled") and not inbound.get("enabled"):
            errors.append("EMAIL_TRANSPORT_NOT_ENABLED")
        for key in ("username_ref", "password_ref"):
            if outbound.get("smtp", {}).get(key, "").strip() == "":
                errors.append(f"SMTP_{key.upper()}_MISSING")
        for key in ("oauth_client_secret_ref", "oauth_token_ref"):
            if inbound.get(key, "").strip() == "":
                errors.append(f"GMAIL_{key.upper()}_MISSING")
    if mode == "fixture" and (root.get("outbound", {}).get("enabled") or root.get("inbound", {}).get("enabled")):
        errors.append("FIXTURE_MODE_NETWORK_TRANSPORT")
    return tuple(errors)
