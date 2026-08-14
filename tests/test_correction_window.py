from datetime import datetime, timedelta, timezone

from sentinel_edge.qualification.correction_window import CorrectionAction, CorrectionWindowPolicy, evaluate_correction_window


def test_late_remote_data_outside_window_is_history_only() -> None:
    event = datetime(2026, 8, 13, tzinfo=timezone.utc)
    decision = evaluate_correction_window(event, event + timedelta(hours=2), CorrectionWindowPolicy(max_lateness_seconds=60))
    assert decision.action is CorrectionAction.HISTORY_ONLY
    assert decision.retroactive_notification_allowed is False


def test_data_inside_window_can_enter_live_path() -> None:
    event = datetime(2026, 8, 13, tzinfo=timezone.utc)
    decision = evaluate_correction_window(event, event + timedelta(seconds=30), CorrectionWindowPolicy(max_lateness_seconds=60))
    assert decision.action is CorrectionAction.LIVE
