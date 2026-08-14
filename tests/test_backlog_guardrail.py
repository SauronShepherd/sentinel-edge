import pytest

from sentinel_edge.qualification.backlog_guardrail import admit_catch_up_burst


def test_catch_up_burst_stays_below_tier_a_reserved_capacity() -> None:
    result = admit_catch_up_burst(backlog_items=100, requested_rate_per_second=20, tier_a_reserved_rate_per_second=8)
    assert result.admitted_rate_per_second == 7
    assert result.protected_service_preserved is True
    assert result.deferred_items == 93


def test_catch_up_burst_rejects_zero_tier_a_capacity() -> None:
    with pytest.raises(ValueError):
        admit_catch_up_burst(backlog_items=1, requested_rate_per_second=1, tier_a_reserved_rate_per_second=0)
