from datetime import datetime, timedelta, timezone

from sentinel_edge.qualification import ReferenceEvent, ReferenceProvider, corroborate_post_event


def test_post_event_corroboration_is_labelled_and_preserves_caveats() -> None:
    local = datetime(2026, 8, 12, 13, 0, tzinfo=timezone.utc)
    report = corroborate_post_event(local, (
        ReferenceEvent(provider=ReferenceProvider.IGN, event_id="ign-1", occurred_at=local + timedelta(seconds=20), published_at=local + timedelta(minutes=3), resolution_km=8.0),
        ReferenceEvent(provider=ReferenceProvider.USGS, event_id="usgs-1", occurred_at=local + timedelta(seconds=200)),
    ))
    assert report.corroborated is True
    assert report.classification == "reference_only"
    assert report.providers_considered == (ReferenceProvider.IGN, ReferenceProvider.USGS)
    assert report.matches[0].status == "matched"
    assert report.matches[0].publication_delay_seconds == 160.0
    assert "reference_only_no_physical_truth_claim" in report.matches[1].caveats
    assert "publication_delay_unknown" in report.matches[1].caveats


def test_post_event_corroboration_rejects_invalid_publication_order_and_unmatched_event() -> None:
    local = datetime(2026, 8, 12, 13, 0, tzinfo=timezone.utc)
    report = corroborate_post_event(local, (
        ReferenceEvent(provider=ReferenceProvider.USGS, event_id="bad", occurred_at=local, published_at=local - timedelta(seconds=1)),
        ReferenceEvent(provider=ReferenceProvider.IGN, event_id="far", occurred_at=local + timedelta(hours=1)),
    ))
    assert report.corroborated is False
    assert all(item.status == "not_matched" for item in report.matches)
    assert "publication_time_precedes_event_time_invalid" in report.matches[0].caveats
