from sentinel_edge.qualification.metadata_conflicts import MetadataAssertion, MetadataDecision, resolve_metadata


def test_conflicting_metadata_preserves_all_sources_and_requires_review() -> None:
    result = resolve_metadata("resolution", [MetadataAssertion("catalogue", "10m"), MetadataAssertion("payload", "20m")], precedence=("payload",))
    assert result.decision is MetadataDecision.REVIEW_REQUIRED
    assert len(result.assertions) == 2
    assert result.value is None


def test_matching_metadata_can_use_declared_precedence() -> None:
    result = resolve_metadata("version", [MetadataAssertion("docs", "v1"), MetadataAssertion("payload", "v1")], precedence=("payload",))
    assert result.decision is MetadataDecision.ACCEPTED
    assert result.value == "v1"
