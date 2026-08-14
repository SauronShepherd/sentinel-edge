import pytest

from sentinel_edge.qualification.cv_ablation import CvAblationReport


def test_cv_ablation_covers_complete_pipeline_and_fallback() -> None:
    report = CvAblationReport("Pi5", True, "kleidicv", "opencv", "wildfire-postprocess", True)
    assert report.complete_pipeline_effect()["stages"] == ["kleidicv", "opencv", "wildfire-postprocess"]
    assert report.complete_pipeline_effect()["fallback_used"] is True


def test_external_benchmark_inheritance_is_rejected() -> None:
    with pytest.raises(ValueError, match="external benchmark"):
        CvAblationReport("Pi5", True, "a", "b", "c", False, external_benchmark_inherited=True)
