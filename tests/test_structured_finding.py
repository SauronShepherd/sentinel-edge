from datetime import datetime, timezone

import pytest

from sentinel_edge.qualification.structured_finding import StructuredFinding


def test_structured_finding_preserves_explicit_claim_dimensions() -> None:
    finding = StructuredFinding(finding_id="f-1", subject="camera-1", predicate="observes",
        object_or_value="smoke", event_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        location="sector-3", uncertainty=.2, source_evidence_id="e-1")
    assert finding.subject == "camera-1"
    assert finding.predicate == "observes"
    assert finding.object_or_value == "smoke"
    assert finding.location == "sector-3"


def test_structured_finding_requires_core_dimensions() -> None:
    with pytest.raises(ValueError):
        StructuredFinding(finding_id="f-1", subject=" ", predicate="observes",
            object_or_value="smoke", uncertainty=.2, source_evidence_id="e-1")
