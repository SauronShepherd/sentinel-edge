from datetime import datetime, timedelta, timezone

import pytest

from sentinel_edge.integrations import SourceSnapshot


def test_source_snapshot_contains_complete_timing_schema() -> None:
    observed = datetime(2026, 8, 12, 10, 0, tzinfo=timezone.utc)
    snapshot = SourceSnapshot(
        source_id="aemet-fire-risk", observed_at=observed,
        published_at=observed + timedelta(minutes=1),
        fetched_at=observed + timedelta(minutes=2),
        expires_at=observed + timedelta(hours=1), payload_sha256="a" * 64,
    )
    assert {"observed_at", "published_at", "fetched_at", "expires_at"} <= set(snapshot.model_dump())


def test_source_snapshot_rejects_incomplete_or_invalid_timeline() -> None:
    observed = datetime(2026, 8, 12, 10, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="fetched_at cannot precede published_at"):
        SourceSnapshot(
            source_id="source", observed_at=observed,
            published_at=observed + timedelta(minutes=2),
            fetched_at=observed + timedelta(minutes=1),
            expires_at=observed + timedelta(hours=1), payload_sha256="a" * 64,
        )
    with pytest.raises(ValueError):
        SourceSnapshot.model_validate({"source_id": "source", "observed_at": observed})
