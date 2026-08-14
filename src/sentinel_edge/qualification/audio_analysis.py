"""Bounded speech and sound-event segment contract."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AudioSegment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    start_seconds: float = Field(ge=0.0)
    end_seconds: float = Field(gt=0.0)
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    language: str | None = None
    transcript: str | None = None

    @model_validator(mode="after")
    def validate_segment(self) -> "AudioSegment":
        if self.end_seconds <= self.start_seconds or not self.label.strip():
            raise ValueError("audio segment bounds and label are required")
        if self.transcript is not None and not self.language:
            raise ValueError("transcript segments require language")
        return self


class BoundedAudioAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    profile_id: str
    segments: tuple[AudioSegment, ...]
    quality_flags: tuple[str, ...] = ()
    abstained: bool = False

    @model_validator(mode="after")
    def validate_analysis(self) -> "BoundedAudioAnalysis":
        if not self.profile_id.strip() or not self.segments:
            raise ValueError("audio profile and at least one segment are required")
        if self.abstained and not self.quality_flags:
            raise ValueError("audio abstention requires a quality flag")
        return self
