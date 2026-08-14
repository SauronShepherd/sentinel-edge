"""Machine-readable timer classes and same-boot authority decisions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TimerClass(StrEnum):
    MONOTONIC_EPHEMERAL = "monotonic-ephemeral"
    TRUSTED_UTC_PERSISTENT = "trusted-utc-persistent"
    RETENTION_SAFETY = "retention-safety"


@dataclass(frozen=True)
class TimerPolicy:
    artifact_grant: TimerClass = TimerClass.MONOTONIC_EPHEMERAL
    source_ttl: TimerClass = TimerClass.TRUSTED_UTC_PERSISTENT
    offline_command: TimerClass = TimerClass.MONOTONIC_EPHEMERAL
    session: TimerClass = TimerClass.MONOTONIC_EPHEMERAL
    outbox_expiry: TimerClass = TimerClass.TRUSTED_UTC_PERSISTENT
    artifact_retention: TimerClass = TimerClass.RETENTION_SAFETY

    def as_dict(self) -> dict[str, str]:
        return {name: value.value for name, value in self.__dict__.items()}


@dataclass(frozen=True)
class AuthorityDecision:
    allowed: bool
    reason: str


def cross_reboot_high_impact(*, utc_trusted: bool, stale: bool) -> AuthorityDecision:
    if not utc_trusted:
        return AuthorityDecision(False, "reconfirmation_required_uncertain_utc")
    if stale:
        return AuthorityDecision(False, "reconfirmation_required_stale_action")
    return AuthorityDecision(True, "cross_reboot_authority_valid")


def retention_gc_allowed(*, utc_trusted: bool, minimum_age_met: bool,
                         wall_clock_expired: bool) -> AuthorityDecision:
    if not minimum_age_met:
        return AuthorityDecision(False, "minimum_retention_age_not_met")
    if wall_clock_expired and not utc_trusted:
        return AuthorityDecision(False, "untrusted_wall_clock_cannot_trigger_gc")
    return AuthorityDecision(True, "retention_gc_allowed")


def source_freshness_allowed(*, utc_trusted: bool, age_known: bool,
                             ttl_seconds: int, age_seconds: float) -> AuthorityDecision:
    if not utc_trusted or not age_known:
        return AuthorityDecision(False, "source_freshness_uncertain")
    if ttl_seconds <= 0 or age_seconds > ttl_seconds:
        return AuthorityDecision(False, "source_stale")
    return AuthorityDecision(True, "source_fresh")


def same_boot_authority(*, issued_monotonic_ns: int, now_monotonic_ns: int,
                        issued_boot_id: str, now_boot_id: str,
                        expires_monotonic_ns: int) -> AuthorityDecision:
    if not issued_boot_id.strip() or not now_boot_id.strip():
        return AuthorityDecision(False, "boot_identity_missing")
    if issued_boot_id != now_boot_id:
        return AuthorityDecision(False, "reconfirmation_required_after_reboot")
    if now_monotonic_ns < issued_monotonic_ns:
        return AuthorityDecision(False, "monotonic_clock_rollback")
    if now_monotonic_ns >= expires_monotonic_ns:
        return AuthorityDecision(False, "same_boot_authority_expired")
    return AuthorityDecision(True, "same_boot_authority_valid")
