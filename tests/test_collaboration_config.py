from pathlib import Path
import yaml


def test_collaboration_config_is_disabled_and_privacy_safe_by_default():
    config = yaml.safe_load(Path("config/collaboration.yaml").read_text())
    collaboration = config["collaboration"]
    consent = collaboration["consent"]
    assert collaboration["enabled"] is False
    assert collaboration["mode"] == "disabled"
    assert consent["sharing_enabled"] is False
    assert consent["research_enabled"] is False
    assert set(consent["hazards"]) == {"wildfire", "earthquake", "flood", "landslide"}
    assert collaboration["privacy"]["node_pseudonym_ref"].startswith("secret://collaboration/")
    assert all(collaboration["privacy"][key] is False for key in ("exact_coordinates_allowed", "raw_sensor_data_allowed", "raw_media_allowed", "raw_waveforms_allowed"))
    assert collaboration["outbound"]["max_email_bytes"] == 65536
    assert collaboration["outbound"]["max_json_payload_bytes"] == 16384
    assert collaboration["inbound"]["poll_interval_seconds"] == 30
    assert collaboration["outbound"]["smtp"]["password_ref"].startswith("secret://")
    assert collaboration["inbound"]["oauth_token_ref"].startswith("secret://")
