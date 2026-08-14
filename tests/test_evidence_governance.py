import pytest

from sentinel_edge.qualification.evidence_governance import (
    BiasRecord,
    LicenceRecord,
    LicenceSubject,
    SubgroupMetric,
    validate_subgroup_metrics,
)


def test_subgroup_failure_cannot_be_hidden_by_aggregate() -> None:
    ok, reasons = validate_subgroup_metrics(
        (SubgroupMetric("site-a", 20, 0.95, 0.01, 0.02), SubgroupMetric("camera-night", 20, 0.4, 0.1, 0.2)),
        critical_subgroups=frozenset({"site-a", "camera-night"}),
    )
    assert ok is False
    assert "critical_subgroup_failed:camera-night" in reasons


def test_bias_and_licences_are_explicitly_separate() -> None:
    bias = BiasRecord("europe-only", "curated-catalogue", "news-reporting", "unreported-events-unknown")
    article = LicenceRecord(LicenceSubject.ARTICLE, "CC-BY-4.0", "https://example.test/article", False, False)
    weights = LicenceRecord(LicenceSubject.MODEL_WEIGHTS, "MIT", "https://example.test/weights", True, True)
    assert bias.missing_observation == "unreported-events-unknown"
    assert article.subject is LicenceSubject.ARTICLE
    assert weights.subject is LicenceSubject.MODEL_WEIGHTS
    assert article.deployment_allowed is False


def test_licence_metadata_is_required() -> None:
    with pytest.raises(ValueError):
        LicenceRecord(LicenceSubject.DATASET, "", "", False, False)
