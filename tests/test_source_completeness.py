from sentinel_edge.integrations.source_quality import SourceCompleteness, assess_source_completeness


def test_http_success_does_not_hide_partial_scientific_coverage() -> None:
    assert assess_source_completeness(transport_status=200, expected_items=10, received_items=4) is SourceCompleteness.PARTIAL
    assert assess_source_completeness(transport_status=200, expected_items=None, received_items=None) is SourceCompleteness.UNKNOWN
    assert assess_source_completeness(transport_status=200, expected_items=10, received_items=10) is SourceCompleteness.COMPLETE
