from sentinel_edge.security.notification_privacy import lock_screen_notification


def test_lock_screen_notification_hides_sensitive_details() -> None:
    item = lock_screen_notification(hazard="wildfire", state="critical", sensitive=True)
    assert item.sensitive_details_hidden is True
    assert "wildfire" not in item.body and "critical" not in item.body


def test_non_sensitive_notification_can_remain_concise_and_informative() -> None:
    item = lock_screen_notification(hazard="status", state="ready", sensitive=False)
    assert item.sensitive_details_hidden is False
    assert item.title.endswith("status") and item.body == "ready"
