import pytest

from sentinel_edge.integrations import ProviderAdvisory, SourceQualityAssessment, invalidate_fixture_on_transition


def test_reachable_degraded_provider_is_not_healthy() -> None:
    assessment = SourceQualityAssessment(True, True, True, ProviderAdvisory.DEGRADED)
    assert assessment.healthy is False
    assert "provider_advisory:degraded" in assessment.reason_codes()


def test_source_transition_invalidates_old_fixture_qualification() -> None:
    result = invalidate_fixture_on_transition("gfm-v1", "gfm-v2")
    assert result.invalidated is True
    assert "fixture_requalification_required" in result.reason_codes


def test_source_fingerprints_are_required() -> None:
    with pytest.raises(ValueError):
        invalidate_fixture_on_transition("", "gfm-v2")
