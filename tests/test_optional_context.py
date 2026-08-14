import pytest

from sentinel_edge.integrations import EidaNetworkRecord, WIS2ContextItem


def test_wis2_context_preserves_identity_and_is_not_h0_dependency() -> None:
    item = WIS2ContextItem("item-1", "centre-a", "weather/topic", "meta-1", "CC-BY")
    assert item.h0_dependency is False
    assert item.optional is True


def test_eida_records_rights_and_availability_without_trigger_authority() -> None:
    record = EidaNetworkRecord("IV", "station-1", "research-only", "available")
    assert record.local_trigger_dependency is False
    assert record.evaluation_only is True


def test_context_records_require_rights_identity() -> None:
    with pytest.raises(ValueError):
        WIS2ContextItem("", "centre", "topic", "meta", "licence")


def test_wis2_normalized_context_traces_to_originating_metadata() -> None:
    item = WIS2ContextItem("item-1", "centre", "topic", "meta-1", "CC-BY")
    normalized = item.normalized_context()
    assert item.trace_normalized_context(normalized) is True
    normalized["metadata_id"] = "mutated"
    assert item.trace_normalized_context(normalized) is False
