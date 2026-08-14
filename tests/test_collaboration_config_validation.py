from pathlib import Path
import yaml
from sentinel_edge.collaboration import validate_collaboration_config


def _hazards():
    return {"wildfire": True, "earthquake": True, "flood": True, "landslide": True}


def test_disabled_profile_is_valid_without_resolved_credentials():
    raw = yaml.safe_load(Path("config/collaboration.yaml").read_text())
    assert validate_collaboration_config(raw) == ()


def test_invalid_research_and_privacy_are_rejected():
    errors = validate_collaboration_config({"collaboration": {"enabled": True, "mode": "fixture", "consent": {"sharing_enabled": False, "research_enabled": True, "hazards": _hazards()}, "privacy": {"raw_media_allowed": True}}})
    assert "RESEARCH_REQUIRES_SHARING" in errors
    assert "PRIVACY_RAW_MEDIA_ALLOWED_FORBIDDEN" in errors


def test_email_mode_requires_only_enabled_transport_refs():
    errors = validate_collaboration_config({"collaboration": {"enabled": True, "mode": "email_experimental", "consent": {"sharing_enabled": True, "research_enabled": False, "hazards": _hazards()}, "privacy": {}, "outbound": {"enabled": True, "smtp": {}}, "inbound": {"enabled": False}}})
    assert {"SMTP_HOST_MISSING", "SMTP_SECURITY_INVALID", "SMTP_USERNAME_REF_MISSING", "SMTP_PASSWORD_REF_MISSING"} <= set(errors)
    assert not any(code.startswith("GMAIL_") for code in errors)


def test_fixture_mode_rejects_network_transport_and_requires_four_hazards():
    errors = validate_collaboration_config({"collaboration": {"enabled": True, "mode": "fixture", "consent": {"sharing_enabled": True, "research_enabled": False, "hazards": {"earthquake": True}}, "outbound": {"enabled": True}}})
    assert "CONSENT_HAZARDS_MUST_COVER_EXACTLY_FOUR" in errors
    assert "FIXTURE_MODE_NETWORK_TRANSPORT" in errors
