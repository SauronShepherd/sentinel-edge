from datetime import datetime, timezone

from fastapi.testclient import TestClient

from sentinel_edge.gateway import create_app


def test_collaboration_api_is_opt_in_and_does_not_expose_secrets(operator_headers):
    client = TestClient(create_app())
    response = client.get("/v1/collaboration/status", headers=operator_headers)
    assert response.status_code == 200
    assert response.json()["sharing_enabled"] is False
    assert response.json()["transport_trust"] == "email_unverified"
    assert "token" not in response.text.lower()


def test_collaboration_consent_requires_valid_separation(admin_headers):
    client = TestClient(create_app())
    payload = {"sharing_enabled": False, "research_enabled": True, "hazards": {"wildfire": True, "earthquake": False, "flood": False, "landslide": False}, "policy_version": "collab-demo-v1", "updated_at": datetime.now(timezone.utc).isoformat()}
    response = client.put("/v1/collaboration/consent", json=payload, headers=admin_headers)
    assert response.status_code == 422


def test_collaboration_consent_can_be_saved_by_governed_operator(admin_headers):
    client = TestClient(create_app())
    payload = {"sharing_enabled": True, "research_enabled": False, "hazards": {"wildfire": True, "earthquake": False, "flood": False, "landslide": False}, "policy_version": "collab-demo-v1", "updated_at": datetime.now(timezone.utc).isoformat()}
    response = client.put("/v1/collaboration/consent", json=payload, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["consent"]["sharing_enabled"] is True
    assert response.json()["audit_required"] is True
    assert response.json()["audit"]["audit_id"] == "collaboration-consent-1"
    status = client.get("/v1/collaboration/status", headers=admin_headers)
    assert status.json()["audit_entries"] == 1
    assert status.json()["last_audit"]["actor"]


def test_collaboration_read_projections_are_explicitly_non_trusted(operator_headers):
    client = TestClient(create_app())
    correlations = client.get("/v1/collaboration/correlations", headers=operator_headers)
    assert correlations.status_code == 200
    assert correlations.json()["trusted_multi_node_confirmation"] is False
    incident = client.get("/v1/incidents/demo-incident/collaboration", headers=operator_headers)
    assert incident.status_code == 200
    assert incident.json()["policy_id"] == "collab-demo-v1"


def test_collaboration_signal_projection_has_bounded_filters_and_cursor(operator_headers):
    client = TestClient(create_app())
    response = client.get("/v1/collaboration/signals?hazard=wildfire&limit=200&cursor=0", headers=operator_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 200 and body["cursor"] == 0
    assert body["total_matching"] == 0
    assert "raw_mime" not in body and "oauth_token" not in response.text.lower()
