"""Bounded video sampling and temporal-coverage contract."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class VideoSamplingPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_id: str
    keyframe_interval_seconds: float = Field(gt=0.0)
    clip_duration_seconds: float = Field(gt=0.0)
    audio_segment_seconds: float = Field(gt=0.0)
    skipped_intervals: tuple[tuple[float, float], ...] = ()
    sampled_intervals: tuple[tuple[float, float], ...]
    source_duration_seconds: float = Field(gt=0.0)

    @model_validator(mode="after")
    def validate_policy(self) -> "VideoSamplingPolicy":
        if not self.policy_id.strip() or not self.sampled_intervals:
            raise ValueError("video sampling policy and sampled intervals are required")
        for start, end in self.sampled_intervals + self.skipped_intervals:
            if start < 0 or end <= start or end > self.source_duration_seconds:
                raise ValueError("video intervals must be bounded by source duration")
        return self

    @property
    def sampled_seconds(self) -> float:
        return sum(end - start for start, end in self.sampled_intervals)

    @property
    def temporal_coverage(self) -> float:
        return min(1.0, self.sampled_seconds / self.source_duration_seconds)
