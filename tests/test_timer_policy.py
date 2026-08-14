from sentinel_edge.runtime.timer_policy import (
    TimerClass, TimerPolicy, cross_reboot_high_impact, retention_gc_allowed,
    same_boot_authority, source_freshness_allowed,
)


def test_timer_policy_covers_required_expiry_classes() -> None:
    assert set(TimerPolicy().as_dict()) == {
        "artifact_grant", "source_ttl", "offline_command", "session",
        "outbox_expiry", "artifact_retention",
    }
    assert TimerPolicy().artifact_retention is TimerClass.RETENTION_SAFETY


def test_same_boot_authority_uses_monotonic_time_and_boot_identity() -> None:
    assert same_boot_authority(issued_monotonic_ns=10, now_monotonic_ns=20,
        issued_boot_id="boot-a", now_boot_id="boot-a", expires_monotonic_ns=30).allowed
    for kwargs in (
        {"issued_boot_id": "boot-a", "now_boot_id": "boot-b", "now_monotonic_ns": 20},
        {"issued_boot_id": "boot-a", "now_boot_id": "boot-a", "now_monotonic_ns": 5},
        {"issued_boot_id": "boot-a", "now_boot_id": "boot-a", "now_monotonic_ns": 30},
    ):
        result = same_boot_authority(issued_monotonic_ns=10, expires_monotonic_ns=30, **kwargs)
        assert result.allowed is False


def test_missing_boot_identity_fails_closed() -> None:
    result = same_boot_authority(issued_monotonic_ns=0, now_monotonic_ns=1,
        issued_boot_id="", now_boot_id="boot", expires_monotonic_ns=2)
    assert result.allowed is False
    assert result.reason == "boot_identity_missing"


def test_cross_reboot_actions_require_trusted_time_and_reconfirmation() -> None:
    assert not cross_reboot_high_impact(utc_trusted=False, stale=False).allowed
    assert not cross_reboot_high_impact(utc_trusted=True, stale=True).allowed
    assert cross_reboot_high_impact(utc_trusted=True, stale=False).allowed


def test_retention_gc_cannot_use_an_untrusted_forward_wall_clock_step() -> None:
    assert not retention_gc_allowed(utc_trusted=False, minimum_age_met=False, wall_clock_expired=True).allowed
    assert not retention_gc_allowed(utc_trusted=False, minimum_age_met=True, wall_clock_expired=True).allowed
    assert retention_gc_allowed(utc_trusted=True, minimum_age_met=True, wall_clock_expired=True).allowed


def test_source_freshness_becomes_uncertain_when_age_cannot_be_defended() -> None:
    assert not source_freshness_allowed(utc_trusted=False, age_known=True, ttl_seconds=60, age_seconds=1).allowed
    assert not source_freshness_allowed(utc_trusted=True, age_known=False, ttl_seconds=60, age_seconds=1).allowed
    assert not source_freshness_allowed(utc_trusted=True, age_known=True, ttl_seconds=60, age_seconds=61).allowed
    assert source_freshness_allowed(utc_trusted=True, age_known=True, ttl_seconds=60, age_seconds=1).allowed
