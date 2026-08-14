from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4
from typing import Any

from sentinel_edge.domain.models import (
    AnalysisResult,
    CoverageState,
    HazardKind,
    IncidentState,
    NotificationStatus,
    ReviewAction,
    ReviewActionKind,
)
from sentinel_edge.incidents import IncidentEventEngine, InMemoryIdempotentNotificationSink
from sentinel_edge.storage import IncidentJournalStore


def analysis(state: IncidentState, score: float = 0.8) -> AnalysisResult:
    return AnalysisResult(
        analysis_id=uuid4(),
        observation_id=uuid4(),
        correlation_id=uuid4(),
        boot_id="boot-review",
        hazard=HazardKind.WILDFIRE,
        score=score,
        state_hint=state,
        features={"signal": score},
        coverage=CoverageState.SUFFICIENT,
    )


def test_notifications_are_grouped_and_dispatch_is_idempotent(tmp_path: Path) -> None:
    store_path = tmp_path / "incidents.sqlite3"
    now = datetime(2026, 8, 2, 10, 0, tzinfo=timezone.utc)
    engine = IncidentEventEngine(IncidentJournalStore(store_path))
    first = engine.apply_analysis(analysis(IncidentState.SUSPECTED), now)
    engine.apply_analysis(analysis(IncidentState.SUSPECTED), now + timedelta(seconds=1))
    assert len(engine.notifications()) == 1

    restarted = IncidentEventEngine(IncidentJournalStore(store_path))
    sink = InMemoryIdempotentNotificationSink()
    delivered = restarted.dispatch_notifications(sink.send)
    assert len(delivered) == 1
    assert delivered[0].status is NotificationStatus.DELIVERED
    assert restarted.dispatch_notifications(sink.send) == ()
    assert sink.effects == [delivered[0].idempotency_key]
    assert restarted.current()[0].incident_id == first.incident_id


def test_snooze_is_audited_but_confirmation_overrides_suppression(tmp_path: Path) -> None:
    now = datetime(2026, 8, 2, 10, 0, tzinfo=timezone.utc)
    engine = IncidentEventEngine(IncidentJournalStore(tmp_path / "incidents.sqlite3"))
    current = engine.apply_analysis(analysis(IncidentState.WATCH, 0.4), now)
    engine.review(
        ReviewAction(
            incident_id=current.incident_id,
            hazard=current.hazard,
            action=ReviewActionKind.SNOOZE,
            actor="operator-a",
            created_at=now + timedelta(seconds=1),
            snooze_until=now + timedelta(minutes=10),
        )
    )
    suspected = engine.apply_analysis(analysis(IncidentState.SUSPECTED, 0.7), now + timedelta(seconds=2))
    assert suspected.state is IncidentState.SUSPECTED
    assert engine.notifications()[-1].status is NotificationStatus.SUPPRESSED

    confirmed = engine.apply_analysis(analysis(IncidentState.CONFIRMED, 0.95), now + timedelta(seconds=3))
    assert confirmed.state is IncidentState.CONFIRMED
    assert engine.notifications()[-1].status is NotificationStatus.PENDING
    assert "snooze_overridden_by_confirmation" in engine.notifications()[-1].reason_codes
    positions = [item.position for item in engine.authority_journal()]
    assert positions == list(range(1, len(positions) + 1))
    assert engine.review_state(str(current.incident_id)).snoozed_by == "operator-a"


def test_delivery_failure_dead_letters_without_rolling_back_incident(tmp_path: Path) -> None:
    engine = IncidentEventEngine(IncidentJournalStore(tmp_path / "incidents.sqlite3"))
    current = engine.apply_analysis(analysis(IncidentState.SUSPECTED))

    def fail(_intent: Any) -> None:
        raise RuntimeError("target unavailable")

    engine.dispatch_notifications(fail)
    engine.dispatch_notifications(fail)
    engine.dispatch_notifications(fail)
    notification = engine.notifications()[0]
    assert notification.status is NotificationStatus.DEAD_LETTER
    assert notification.attempt_count == 3
    assert engine.current()[0].incident_id == current.incident_id
    assert engine.current()[0].state is IncidentState.SUSPECTED
    assert engine.notification_metrics()["dead_letter"] == 1


def test_correction_storm_is_bounded_but_material_confirmation_remains_visible(tmp_path: Path) -> None:
    engine = IncidentEventEngine(IncidentJournalStore(tmp_path / "incidents.sqlite3"), notification_budget=1)
    now = datetime(2026, 8, 2, 10, 0, tzinfo=timezone.utc)
    engine.apply_analysis(analysis(IncidentState.SUSPECTED), now)
    watch = engine.apply_analysis(analysis(IncidentState.WATCH, 0.5), now + timedelta(seconds=1))
    assert watch.state is IncidentState.WATCH
    assert len(engine.notifications()) == 2
    assert engine.notifications()[-1].status is NotificationStatus.SUPPRESSED
    confirmed = engine.apply_analysis(analysis(IncidentState.CONFIRMED, 0.95), now + timedelta(seconds=2))
    assert confirmed.state is IncidentState.CONFIRMED
    assert engine.notifications()[-1].status is NotificationStatus.PENDING
