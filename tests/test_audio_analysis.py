import pytest

from sentinel_edge.qualification.audio_analysis import AudioSegment, BoundedAudioAnalysis


def test_audio_analysis_preserves_transcript_language_and_sound_segments() -> None:
    result = BoundedAudioAnalysis(profile_id="audio-v1", segments=(
        AudioSegment(start_seconds=0, end_seconds=2.5, label="speech", confidence=.9,
            language="es", transcript="ayuda"),
        AudioSegment(start_seconds=3, end_seconds=4, label="siren", confidence=.7),
    ))
    assert result.segments[0].language == "es"
    assert result.segments[0].start_seconds == 0
    assert result.segments[1].label == "siren"


def test_audio_transcript_requires_language_and_valid_bounds() -> None:
    with pytest.raises(ValueError):
        AudioSegment(start_seconds=1, end_seconds=1, label="speech", confidence=.5)
    with pytest.raises(ValueError):
        AudioSegment(start_seconds=0, end_seconds=1, label="speech", confidence=.5, transcript="hola")
