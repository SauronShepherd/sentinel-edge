from datetime import datetime, timezone
from uuid import uuid4

import pytest

from sentinel_edge.exports import (
    CapDraftValidationError,
    build_cap_test_draft,
    validate_cap_test_document,
    write_cap_test_draft,
)


def test_cap_test_draft_is_schema_valid_and_explicitly_non_sendable(tmp_path) -> None:
    draft = build_cap_test_draft(
        incident_id=uuid4(),
        sender="sentinel-edge.local",
        event="Smoke-like observation",
        description="Review-only local observation.",
        sent=datetime(2026, 8, 12, 10, 0, tzinfo=timezone.utc),
    )
    assert draft.status == "Test"
    assert draft.sendable is False
    report = validate_cap_test_document(draft.xml)
    assert report["status"] == "Test"
    assert report["sendable"] is False
    output = write_cap_test_draft(draft, tmp_path / "alert.xml")
    assert output.read_bytes() == draft.xml


def test_cap_validator_rejects_non_test_status() -> None:
    draft = build_cap_test_draft(
        incident_id=uuid4(), sender="sender", event="event", description="description"
    )
    tampered = draft.xml.replace(b">Test<", b">Actual<")
    with pytest.raises(CapDraftValidationError, match="status=Test"):
        validate_cap_test_document(tampered)
