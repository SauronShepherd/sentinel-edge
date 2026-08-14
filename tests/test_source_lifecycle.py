from sentinel_edge.integrations import ProcessingClass, SourceProduct, evaluate_source_transition
from datetime import datetime, timezone


def product(version: str, processing: ProcessingClass = ProcessingClass.OPERATIONAL_NRT) -> SourceProduct:
    return SourceProduct("firms", "api-v1", version, "terms-v1", processing, "centre-a", "topic-a", "meta-a", "CC-BY", "interface-sha256:v1", datetime(2025, 1, 1, tzinfo=timezone.utc))


def test_behavior_changing_source_transition_requires_review() -> None:
    transition = evaluate_source_transition(product("v1"), product("v2"))
    assert transition.review_required is True
    assert "product_version_changed" in transition.reason_codes


def test_processing_class_lineage_remains_distinguishable() -> None:
    transition = evaluate_source_transition(product("v1"), product("v1", ProcessingClass.STANDARD_SCIENCE))
    assert transition.review_required is True
    assert "processing_class_changed" in transition.reason_codes


def test_source_review_date_and_interface_fingerprint_are_recorded() -> None:
    item = product("v1")
    assert item.licence_id == "CC-BY"
    assert item.interface_fingerprint.startswith("interface-sha256:")
    assert item.terms_reviewed_at is not None
