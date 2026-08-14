from datetime import datetime, timezone

import pytest

from sentinel_edge.privacy.location_evidence import LocationEvidence


def test_location_evidence_preserves_time_precision_derivation_and_consent() -> None:
    record = LocationEvidence("reporter-1", datetime(2026, 1, 1, tzinfo=timezone.utc), 40.0, -3.0, 50.0, "device_gnss", "private", "consent-v1")
    assert record.as_evidence()["precision_m"] == 50.0


def test_private_location_without_consent_or_precision_is_rejected() -> None:
    with pytest.raises(ValueError, match="consent"):
        LocationEvidence("r", datetime(2026, 1, 1, tzinfo=timezone.utc), 0, 0, 10, "manual", "private", None)
    with pytest.raises(ValueError, match="precision"):
        LocationEvidence("r", datetime(2026, 1, 1, tzinfo=timezone.utc), 0, 0, 0, "manual", "public", None)
