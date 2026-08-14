from fastapi.testclient import TestClient

from sentinel_edge.domain.models import Observation
from sentinel_edge.gateway import create_app
from sentinel_edge.scenario import DeterministicScenarioEngine, load_scenario


def test_storage_diagnostics_and_checkpoint_are_authorized(
    viewer_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    client = TestClient(create_app())
    response = client.get("/v1/storage", headers=viewer_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["incident_journal"]["durability"]["synchronous"] == 2
    assert body["incident_journal"]["durability"]["journal_mode"] in {"memory", "wal"}
    assert body["incident_journal"]["integrity_check"] == "ok"
    assert body["artifacts"]["reserve_bytes"] > 0

    forbidden = client.post("/v1/storage/checkpoint", json={"mode": "PASSIVE"}, headers=viewer_headers)
    assert forbidden.status_code == 403
    checkpoint = client.post("/v1/storage/checkpoint", json={"mode": "PASSIVE"}, headers=admin_headers)
    assert checkpoint.status_code == 200
    assert checkpoint.json()["mode"] == "PASSIVE"


def test_operator_can_reconcile_bounded_critical_spool(operator_headers: dict[str, str]) -> None:
    engine = DeterministicScenarioEngine()
    raw = load_scenario("fixtures/scenarios/simultaneous-event.json")["observations"][0]
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    observation = Observation.model_validate(raw).model_copy(update={"observed_at": now, "received_at": now})
    analysis = engine.analysis.analyze(observation)
    engine.set_incident_authority_available(False, reason="test_outage")
    engine.apply_or_spool(analysis, observation.received_at)
    client = TestClient(create_app(engine))
    before = client.get("/v1/storage", headers=operator_headers).json()
    assert before["critical_spool"]["pending_items"] == 1
    response = client.post("/v1/critical-spool/reconcile", headers=operator_headers)
    assert response.status_code == 200
    assert response.json()["delivered_analysis_ids"] == [str(analysis.analysis_id)]
    assert response.json()["metrics"]["pending_items"] == 0


def test_incident_projection_exposes_authority_loss_without_inventing_freshness(
    viewer_headers: dict[str, str],
) -> None:
    engine = DeterministicScenarioEngine()
    engine.set_incident_authority_available(False, reason="test_outage")
    client = TestClient(create_app(engine))

    response = client.get("/v1/incidents", headers=viewer_headers)

    assert response.status_code == 200
    assert response.headers["X-Incident-Authority"] == "unavailable"
    assert response.headers["X-Incident-Projection"] == "authoritative-stale"
    assert "test_outage" in response.headers["X-Incident-Authority-Reason"]
