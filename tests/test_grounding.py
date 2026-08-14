from datetime import datetime, timezone

import pytest

from sentinel_edge.qualification.grounding import GroundedValue, GroundingSource


def test_grounding_sources_remain_distinct() -> None:
    claimed = GroundedValue(field="location", value="ridge", source=GroundingSource.CLAIMED,
        confidence=.3, source_evidence_id="e-1")
    confirmed = GroundedValue(field="location", value="ridge", source=GroundingSource.OPERATOR_CONFIRMED,
        confidence=1, source_evidence_id="e-2", confirmed_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert claimed.source is not confirmed.source
    assert confirmed.confirmed_at is not None


def test_operator_confirmation_requires_timestamp() -> None:
    with pytest.raises(ValueError):
        GroundedValue(field="time", value="noon", source=GroundingSource.OPERATOR_CONFIRMED,
            confidence=1, source_evidence_id="e-1")
