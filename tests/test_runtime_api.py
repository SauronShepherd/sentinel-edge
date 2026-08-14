import json

from fastapi.testclient import TestClient

from sentinel_edge.gateway import create_app
from sentinel_edge.scenario import DeterministicScenarioEngine


def test_runtime_capabilities_and_opportunities_are_explicit(operator_headers: dict[str, str]) -> None:
    engine = DeterministicScenarioEngine()
    client = TestClient(create_app(engine))
    scenario = json.load(open("fixtures/scenarios/simultaneous-event.json", encoding="utf-8"))
    response = client.post("/v1/scenarios/run", json=scenario, headers=operator_headers)
    assert response.status_code == 200
    runtime = client.get("/v1/runtime", headers=operator_headers).json()
    assert runtime["overloaded"] is False
    opportunities = client.get("/v1/opportunities", headers=operator_headers).json()
    assert opportunities["reconciliation"]["balanced"] is True
    health = client.get("/health").json()
    ids = {item["capability_id"] for item in health["capabilities"]}
    assert {"acquisition", "analysis", "runtime", "incident_authority", "api", "evidence"} <= ids


def test_dependency_failure_is_user_visible_and_fail_closed(viewer_headers: dict[str, str]) -> None:
    engine = DeterministicScenarioEngine()
    engine.set_incident_authority_available(False, reason="dependency_timeout")
    client = TestClient(create_app(engine))
    health = client.get("/health", headers=viewer_headers)
    assert health.status_code == 200
    body = health.json()
    assert body["status"] == "failed"
    authority = next(item for item in body["capabilities"] if item["capability_id"] == "incident_authority")
    assert authority["state"] == "failed"
    assert authority["consequence"] == "incident lifecycle can be updated and recovered"
    assert authority["reason_codes"] == ["critical_spool_active", "dependency_timeout"]
    projection = client.get("/v1/incidents", headers=viewer_headers)
    assert projection.headers["X-Incident-Authority"] == "unavailable"
    assert projection.headers["X-Incident-Projection"] == "authoritative-stale"
