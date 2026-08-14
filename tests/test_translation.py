import pytest

from sentinel_edge.qualification.translation import DerivedTranslation


def test_translation_retains_original_and_labels_derived_output() -> None:
    result = DerivedTranslation(artifact_id="tr-1", original_text="ayuda", original_language="es",
        translated_text="help", target_language="en", translation_confidence=.88,
        model_version="translate-v1", source_evidence_id="audio-1")
    assert result.original_text == "ayuda"
    assert result.derived is True
    assert result.model_version == "translate-v1"


def test_translation_rejects_same_language() -> None:
    with pytest.raises(ValueError):
        DerivedTranslation(artifact_id="tr-1", original_text="help", original_language="en",
            translated_text="help", target_language="en", translation_confidence=1,
            model_version="v1", source_evidence_id="e-1")
