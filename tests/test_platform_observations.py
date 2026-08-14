from datetime import datetime, timezone

import pytest

from sentinel_edge.qualification.platform_observations import PlatformObservation, observation_at


def test_historical_lookup_keeps_prior_provider_state_after_later_observation() -> None:
    first = PlatformObservation("obs-1", "provider-a", {"version": "1"}, datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 2, 1, tzinfo=timezone.utc))
    later = PlatformObservation("obs-2", "provider-a", {"version": "2"}, datetime(2026, 2, 1, tzinfo=timezone.utc))
    assert observation_at([first, later], datetime(2026, 1, 15, tzinfo=timezone.utc)).state == {"version": "1"}
    assert observation_at([first, later], datetime(2026, 3, 1, tzinfo=timezone.utc)).state == {"version": "2"}


def test_intervals_are_half_open_and_overlap_is_rejected() -> None:
    first = PlatformObservation("obs-1", "p", {"x": 1}, datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 2, 1, tzinfo=timezone.utc))
    second = PlatformObservation("obs-2", "p", {"x": 2}, datetime(2026, 2, 1, tzinfo=timezone.utc))
    assert observation_at([first, second], datetime(2026, 2, 1, tzinfo=timezone.utc)) is second
    overlapping = PlatformObservation("obs-3", "p", {"x": 3}, datetime(2026, 1, 15, tzinfo=timezone.utc))
    with pytest.raises(ValueError, match="overlapping"):
        observation_at([first, overlapping], datetime(2026, 1, 20, tzinfo=timezone.utc))


def test_naive_times_are_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        PlatformObservation("obs", "p", {"x": 1}, datetime(2026, 1, 1))
