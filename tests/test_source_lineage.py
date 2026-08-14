from sentinel_edge.qualification.source_lineage import LineageAggregationReport, SourceSnapshotLineage, evaluate_lineage_influence, fingerprint_source_snapshot


def test_source_snapshot_resolves_to_stable_lineage_fingerprint() -> None:
    first = fingerprint_source_snapshot({"parent": "V07", "constellation": "A", "version": 1})
    second = fingerprint_source_snapshot({"version": 1, "constellation": "A", "parent": "V07"})
    assert first == second
    lineage = SourceSnapshotLineage(source_id="source-1", snapshot_id="snap-1", lineage_fingerprint=first,
        parent_product="V07", constellation="A", algorithm_version="V07")
    assert lineage.lineage_fingerprint == first


def test_mutated_parent_product_removes_decision_influence() -> None:
    original = SourceSnapshotLineage(source_id="s", snapshot_id="a", lineage_fingerprint="a" * 64,
        parent_product="V07", constellation="A", algorithm_version="V07")
    mutated = original.model_copy(update={"parent_product": "V08"})
    decision = evaluate_lineage_influence(original, mutated)
    assert decision.decision_influence_allowed is False
    assert decision.reason == "parent_or_constellation_changed"


def test_lineage_preserves_algorithm_transition() -> None:
    lineage = SourceSnapshotLineage(source_id="s", snapshot_id="b", lineage_fingerprint="b" * 64,
        parent_product="V08", constellation="A", algorithm_version="V08",
        parent_product_transition="V07->V08")
    assert lineage.parent_product_transition == "V07->V08"


def test_lineage_report_prevents_silent_before_after_aggregation() -> None:
    report = LineageAggregationReport(groups={"V07": 3, "V08": 2}, separated_transitions=True)
    assert set(report.groups) == {"V07", "V08"}
