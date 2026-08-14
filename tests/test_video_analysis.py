import pytest

from sentinel_edge.qualification.video_analysis import VideoSamplingPolicy


def test_video_policy_exposes_sampling_skips_and_coverage() -> None:
    policy = VideoSamplingPolicy(policy_id="video-v1", keyframe_interval_seconds=5,
        clip_duration_seconds=2, audio_segment_seconds=4, source_duration_seconds=20,
        sampled_intervals=((0, 2), (10, 12)), skipped_intervals=((2, 10), (12, 20)))
    assert policy.temporal_coverage == pytest.approx(.2)
    assert policy.skipped_intervals == ((2, 10), (12, 20))


def test_video_policy_rejects_out_of_bounds_intervals() -> None:
    with pytest.raises(ValueError):
        VideoSamplingPolicy(policy_id="video-v1", keyframe_interval_seconds=5,
            clip_duration_seconds=2, audio_segment_seconds=4, source_duration_seconds=20,
            sampled_intervals=((0, 21),))
