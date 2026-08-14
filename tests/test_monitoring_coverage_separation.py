from datetime import datetime, timezone
from uuid import uuid4

from sentinel_edge.domain.models import CoverageState, HazardKind, IncidentLabel, IncidentRecord, IncidentState, SourceMode
from sentinel_edge.gateway import create_app


def test_normal_incident_card_can_carry_blind_coverage_independently() -> None:
    record = IncidentRecord(
        incident_id=uuid4(), hazard=HazardKind.WILDFIRE, state=IncidentState.NORMAL,
        confidence=0.0, coverage=CoverageState.BLIND, source_mode=SourceMode.FIXTURE,
        first_observed_at=datetime(2026, 8, 12, tzinfo=timezone.utc),
        last_observed_at=datetime(2026, 8, 12, tzinfo=timezone.utc),
        event_time_watermark=datetime(2026, 8, 12, tzinfo=timezone.utc),
        version=1, labels=(IncidentLabel.REJECT,),
    )
    payload = record.model_dump(mode="json")
    assert payload["state"] == "normal"
    assert payload["coverage"] == "blind"
    assert payload["state"] != payload["coverage"]


def test_ui_contract_names_state_and_coverage_separately() -> None:
    app = create_app()
    html = next(route for route in app.routes if getattr(route, "path", None) == "/client").endpoint()
    body = getattr(html, "body", b"").decode("utf-8")
    assert "Hazard state is separate from monitoring coverage" in body
    assert "/client/app.js" in body
    js = next(route for route in app.routes if getattr(route, "path", None) == "/client/app.js").endpoint()
    script = getattr(js, "body", b"").decode("utf-8")
    assert "<strong>State:</strong>" in script
    assert "<strong>Coverage:</strong>" in script
