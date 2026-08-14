"""Fail-closed validation for the optional collaboration configuration profile."""
from __future__ import annotations

from typing import Any


_SECRET_PREFIX = "secret://collaboration/"


def _consent(root: dict[str, Any]) -> dict[str, Any]:
    """Read the v1 nested consent block while accepting the pre-spec draft shape.

    Compatibility is intentionally read-only: the shipped configuration is the
    normative nested shape from SE-COLLAB-CODEX-001.
    """
    value = root.get("consent")
    if isinstance(value, dict):
        return value
    return {
        "sharing_enabled": root.get("sharing_enabled", False),
        "research_enabled": root.get("research_enabled", False),
        "policy_version": root.get("policy_version", "collab-consent-v1"),
        "hazards": root.get("hazards", {}),
    }


def _valid_secret_ref(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(_SECRET_PREFIX) and len(value) > len(_SECRET_PREFIX)


def validate_collaboration_config(raw: dict[str, Any]) -> tuple[str, ...]:
    root = raw.get("collaboration", raw)
    errors: list[str] = []
    mode = root.get("mode", "disabled")
    enabled = bool(root.get("enabled", False))
    consent = _consent(root)
    sharing = bool(consent.get("sharing_enabled", False))
    research = bool(consent.get("research_enabled", False))

    if mode not in {"disabled", "fixture", "email_experimental"}:
        errors.append("MODE_UNSUPPORTED")
    if research and not sharing:
        errors.append("RESEARCH_REQUIRES_SHARING")

    hazards = consent.get("hazards", {})
    if set(hazards) != {"wildfire", "earthquake", "flood", "landslide"}:
        errors.append("CONSENT_HAZARDS_MUST_COVER_EXACTLY_FOUR")

    privacy = root.get("privacy", {})
    for key in ("exact_coordinates_allowed", "raw_sensor_data_allowed", "raw_media_allowed", "raw_waveforms_allowed"):
        if privacy.get(key, False):
            errors.append(f"PRIVACY_{key.upper()}_FORBIDDEN")
    node_ref = privacy.get("node_pseudonym_ref")
    if node_ref is not None and not _valid_secret_ref(node_ref):
        errors.append("NODE_PSEUDONYM_REF_INVALID")

    if not enabled and mode != "disabled":
        errors.append("DISABLED_MODE_MISMATCH")
    if enabled and mode == "disabled":
        errors.append("ENABLED_MODE_MISMATCH")

    outbound = root.get("outbound", {})
    inbound = root.get("inbound", {})
    if mode == "fixture" and (outbound.get("enabled") or inbound.get("enabled")):
        errors.append("FIXTURE_MODE_NETWORK_TRANSPORT")

    if mode == "email_experimental" and enabled:
        if not sharing:
            errors.append("EMAIL_REQUIRES_SHARING")
        if not outbound.get("enabled") and not inbound.get("enabled"):
            errors.append("EMAIL_TRANSPORT_NOT_ENABLED")
        if outbound.get("enabled"):
            smtp = outbound.get("smtp", {})
            if not str(smtp.get("host", "")).strip():
                errors.append("SMTP_HOST_MISSING")
            if smtp.get("security") not in {"starttls", "tls"}:
                errors.append("SMTP_SECURITY_INVALID")
            for key in ("username_ref", "password_ref"):
                if not _valid_secret_ref(smtp.get(key)):
                    errors.append(f"SMTP_{key.upper()}_MISSING")
        if inbound.get("enabled"):
            for key in ("oauth_client_secret_ref", "oauth_token_ref"):
                if not _valid_secret_ref(inbound.get(key)):
                    errors.append(f"GMAIL_{key.upper()}_MISSING")

    queue = outbound.get("queue", {})
    if queue:
        if not 1 <= int(queue.get("max_items", 0)) <= 1024:
            errors.append("OUTBOUND_QUEUE_SIZE_INVALID")
        if int(queue.get("max_age_seconds", 0)) <= 0:
            errors.append("OUTBOUND_QUEUE_AGE_INVALID")
        if int(queue.get("max_attempts", 0)) <= 0:
            errors.append("OUTBOUND_QUEUE_ATTEMPTS_INVALID")

    if int(outbound.get("max_email_bytes", 65536)) > 65536:
        errors.append("EMAIL_SIZE_BUDGET_EXCEEDED")
    if int(outbound.get("max_json_payload_bytes", 16384)) > 16384:
        errors.append("JSON_SIZE_BUDGET_EXCEEDED")

    return tuple(dict.fromkeys(errors))
