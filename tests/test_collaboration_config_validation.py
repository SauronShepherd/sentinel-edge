from pathlib import Path

import yaml

from sentinel_edge.collaboration import validate_collaboration_config


def test_disabled_profile_is_valid_without_credentials():
    raw = yaml.safe_load(Path("config/collaboration.yaml").read_text())
    assert validate_collaboration_config(raw) == ()


def test_invalid_research_and_privacy_are_rejected():
    errors = validate_collaboration_config({"collaboration": {"enabled": True, "mode": "fixture", "sharing_enabled": False, "research_enabled": True, "privacy": {"raw_media_allowed": True}}})
    assert "RESEARCH_REQUIRES_SHARING" in errors
    assert "PRIVACY_RAW_MEDIA_ALLOWED_FORBIDDEN" in errors


def test_email_mode_requires_explicit_transport_and_refs():
    errors = validate_collaboration_config({"collaboration": {"enabled": True, "mode": "email_experimental", "sharing_enabled": True, "outbound": {"enabled": False, "smtp": {}}, "inbound": {"enabled": False}}})
    assert {"EMAIL_TRANSPORT_NOT_ENABLED", "SMTP_USERNAME_REF_MISSING", "SMTP_PASSWORD_REF_MISSING", "GMAIL_OAUTH_CLIENT_SECRET_REF_MISSING", "GMAIL_OAUTH_TOKEN_REF_MISSING"} <= set(errors)
