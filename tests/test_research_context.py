import pytest

from sentinel_edge.qualification.research_context import ResearchContextRecord


def test_research_context_preserves_provenance_and_offline_scope() -> None:
    record = ResearchContextRecord(dataset_name="UGLC", record_id="r-1", original_provenance="uglc:source:1")
    assert record.offline_fixture is True
    assert record.local_event_truth is False
    assert record.original_provenance == "uglc:source:1"


def test_research_context_cannot_be_promoted_to_event_truth() -> None:
    with pytest.raises(ValueError):
        ResearchContextRecord(dataset_name="Tenerife", record_id="r-1", original_provenance="source",
            local_event_truth=True)
