import pytest

from sentinel_edge.qualification.image_analysis import BoundedImageAnalysis, ImageRegion


def test_bounded_image_analysis_preserves_regions_text_quality_and_confidence() -> None:
    result = BoundedImageAnalysis(profile_id="image-ocr-v1", regions=(ImageRegion(
        label="smoke", x=.1, y=.2, width=.3, height=.4, confidence=.8),),
        text=("EXIT",), ocr_confidence=.9, quality_flags=("sharp",), abstained=False)
    assert result.regions[0].label == "smoke"
    assert result.text == ("EXIT",)


def test_abstention_requires_quality_reason() -> None:
    with pytest.raises(ValueError):
        BoundedImageAnalysis(profile_id="image-v1", abstained=True)
