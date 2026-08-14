import pytest
from pydantic import ValidationError

from sentinel_edge.integrations import OfficialSourceRecord


def test_official_wording_and_severity_are_preserved_when_summary_is_derived() -> None:
    record = OfficialSourceRecord(
        source_id="official-alert-1",
        original_wording="Evacuate the designated zone.",
        official_severity="Extreme",
        derived_summary="Evacuation advised",
    )
    assert record.display_text() == "Evacuate the designated zone."
    assert record.official_severity == "Extreme"
    assert record.model_dump()["original_wording"] == "Evacuate the designated zone."


def test_official_record_rejects_missing_wording_or_severity() -> None:
    with pytest.raises(ValidationError):
        OfficialSourceRecord(source_id="official-alert-1", original_wording="", official_severity="Extreme")
    with pytest.raises(ValidationError):
        OfficialSourceRecord(source_id="official-alert-1", original_wording="text", official_severity="")
