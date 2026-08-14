from datetime import datetime, timedelta, timezone

import pytest

from sentinel_edge.domain.models import TimeOrigin, TimeSourceObservation, TimeTrustState
from sentinel_edge.runtime import TrustedTimeManager


BASE = datetime(2026, 8, 2, 18, 0, tzinfo=timezone.utc)


def source(
    source_id: str,
    origin: TimeOrigin,
    *,
    authenticated: bool,
    utc: datetime = BASE,
    monotonic_ns: int = 1_000_000_000,
    uncertainty_ms: float = 10.0,
    age_ms: float = 0.0,
    continuity_id: str = "boot-1",
    epoch: int = 0,
    bootstrap: bool | None = True,
) -> TimeSourceObservation:
    return TimeSourceObservation(
        source_id=source_id,
        origin=origin,
        authenticated=authenticated,
        observed_utc=utc,
        observed_monotonic_ns=monotonic_ns,
        uncertainty_ms=uncertainty_ms,
        age_ms=age_ms,
        stratum=2 if origin in {TimeOrigin.NTP, TimeOrigin.NTS} else None,
        reference_id="time.example",
        continuity_id=continuity_id,
        clock_epoch=epoch,
        certificate_bootstrap_valid=bootstrap,
    )


def test_unauthenticated_ntp_is_display_only() -> None:
    manager = TrustedTimeManager()
    snapshot = manager.update(source("ntp", TimeOrigin.NTP, authenticated=False))
    assert snapshot.state is TimeTrustState.DISPLAY_ONLY
    assert snapshot.display_time_allowed is True
    assert snapshot.security_validity_allowed is False
    assert snapshot.remote_freshness_allowed is False
    assert snapshot.peer_correlation_allowed is False
    assert "unauthenticated_ntp_cannot_strengthen_security" in snapshot.reason_codes


def test_authenticated_nts_can_support_security_uses() -> None:
    manager = TrustedTimeManager()
    snapshot = manager.update(source("nts", TimeOrigin.NTS, authenticated=True))
    assert snapshot.state is TimeTrustState.TRUSTED
    assert snapshot.security_validity_allowed is True
    assert snapshot.remote_freshness_allowed is True
    assert snapshot.peer_correlation_allowed is True


def test_disagreeing_trusted_sources_create_discontinuity_epoch() -> None:
    manager = TrustedTimeManager()
    first = manager.update(source("nts-a", TimeOrigin.NTS, authenticated=True))
    second = manager.update(source("nts-b", TimeOrigin.NTS, authenticated=True, utc=BASE + timedelta(seconds=5)))
    assert second.clock_epoch > first.clock_epoch
    assert second.security_validity_allowed is False
    assert "trusted_sources_disagree" in second.reason_codes


def test_utc_rollback_is_visible_and_monotonic_rollback_is_rejected() -> None:
    manager = TrustedTimeManager()
    manager.update(source("nts", TimeOrigin.NTS, authenticated=True))
    rolled = manager.update(source(
        "nts", TimeOrigin.NTS, authenticated=True,
        utc=BASE - timedelta(seconds=10), monotonic_ns=2_000_000_000,
    ))
    assert "utc_rollback_detected" in rolled.reason_codes
    assert rolled.clock_epoch >= 1
    with pytest.raises(ValueError, match="monotonic rollback"):
        manager.update(source(
            "nts", TimeOrigin.NTS, authenticated=True,
            utc=BASE + timedelta(seconds=1), monotonic_ns=1,
        ))


def test_invalid_certificate_bootstrap_blocks_trusted_use() -> None:
    manager = TrustedTimeManager()
    snapshot = manager.update(source("nts", TimeOrigin.NTS, authenticated=True, bootstrap=False))
    assert snapshot.state is TimeTrustState.DEGRADED
    assert snapshot.security_validity_allowed is False
    assert "certificate_bootstrap_invalid" in snapshot.reason_codes
