from datetime import datetime, timezone, timedelta

import pytest

from sentinel_edge.qualification.hazard_context import (
    AuthorityNotice, HazardContextProvider, HazardContextRecord, assess_hazard_context,
)


def test_context_exposes_freshness_and_resolution_caveat() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    result = assess_hazard_context((HazardContextRecord(
        provider=HazardContextProvider.AEMET, record_id="a-1",
        observed_at=now - timedelta(minutes=5), received_at=now - timedelta(minutes=4),
        original_provenance="fixture:aemet-1",
    ),), now=now, max_age_seconds=600)
    assert result[0].fresh is True
    assert "spatial_resolution_unknown" in result[0].caveats
    assert result[0].reference_only is True


def test_context_delay_and_resolution_are_visible() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    result = assess_hazard_context((HazardContextRecord(
        provider=HazardContextProvider.FIRMS, record_id="f-1",
        observed_at=now - timedelta(hours=2), received_at=now - timedelta(hours=1),
        resolution_km=1.0, original_provenance="fixture:firms-1",
    ),), now=now, max_age_seconds=600)
    assert result[0].fresh is False
    assert result[0].freshness_seconds == 7200
    assert result[0].resolution_km == 1.0


def test_context_requires_timezone_and_positive_age() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        assess_hazard_context((), now=now, max_age_seconds=0)
    with pytest.raises(ValueError):
        assess_hazard_context((), now=datetime(2026, 1, 1), max_age_seconds=1)


def test_authority_notice_preserves_source_and_provisional_status() -> None:
    notice = AuthorityNotice(
        provider=HazardContextProvider.METEOALARM, notice_id="m-1",
        issued_at=datetime(2026, 1, 1, tzinfo=timezone.utc), status="orange",
        original_authority="MeteoAlarm/AEMET", source_url="fixture://warning",
    )
    assert notice.provisional is True
    assert notice.original_authority == "MeteoAlarm/AEMET"


def test_authority_notice_rejects_missing_authority() -> None:
    with pytest.raises(ValueError):
        AuthorityNotice(
            provider=HazardContextProvider.SAIH, notice_id="s-1",
            issued_at=datetime(2026, 1, 1, tzinfo=timezone.utc), status="watch",
            original_authority=" ",
        )
