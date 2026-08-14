from datetime import datetime, timedelta, timezone

from sentinel_edge.qualification.post_fire_context import PostFireContext, evaluate_post_fire_context


def _context(**kwargs):
    now = datetime(2026, 1, 10, tzinfo=timezone.utc)
    values = dict(fire_id="f1", fire_area=frozenset({"cell-a"}), affected_area=frozenset({"cell-a"}), observed_at=now - timedelta(days=1), now=now)
    values.update(kwargs)
    return PostFireContext(**values)


def test_only_fresh_spatial_overlap_boosts_cadence_and_never_changes_hazard_state() -> None:
    result = evaluate_post_fire_context(_context())
    assert result.cadence_multiplier == 2.0
    assert result.hazard_state_influence is False
    assert "cadence_only" in result.reason_codes


def test_non_overlap_and_expired_context_do_not_boost_cadence() -> None:
    assert evaluate_post_fire_context(_context(affected_area=frozenset({"cell-b"}))).cadence_multiplier == 1.0
    assert evaluate_post_fire_context(_context(observed_at=datetime(2025, 11, 1, tzinfo=timezone.utc))).cadence_multiplier == 1.0
