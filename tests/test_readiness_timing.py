from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from sentinel_edge.qualification.readiness_timing import ReadinessTiming


def test_readiness_timing_exposes_boot_recovery_and_gates() -> None:
    start = datetime(2026, 8, 13, tzinfo=timezone.utc)
    timing = ReadinessTiming(
        boot_started_at=start, ready_at=start + timedelta(seconds=4.5),
        recovery_started_at=start + timedelta(seconds=10), recovery_ready_at=start + timedelta(seconds=13.25),
        readiness_gates=("artifacts", "schemas", "storage", "clock", "minimum_coverage"),
    )
    assert timing.boot_to_ready_seconds == 4.5
    assert timing.recovery_to_ready_seconds == 3.25
    assert timing.transcript()["readiness_gates"][-1] == "minimum_coverage"


def test_readiness_timing_rejects_inverted_transcripts() -> None:
    start = datetime(2026, 8, 13, tzinfo=timezone.utc)
    with pytest.raises(ValidationError):
        ReadinessTiming(
            boot_started_at=start, ready_at=start - timedelta(seconds=1),
            recovery_started_at=start, recovery_ready_at=start,
            readiness_gates=("artifacts",),
        )
