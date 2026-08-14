from fastapi.testclient import TestClient

from sentinel_edge.gateway import create_app


def test_untrusted_host_is_rejected_and_forwarded_headers_do_not_bypass_it() -> None:
    client = TestClient(create_app())
    response = client.get("/health", headers={"host": "evil.example", "x-forwarded-host": "localhost"})
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "host_not_allowed"


def test_cross_origin_request_receives_no_cors_authorization() -> None:
    client = TestClient(create_app())
    response = client.get("/health", headers={"origin": "https://evil.example"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in {key.lower() for key in response.headers}


def test_cross_origin_browser_write_requires_csrf_boundary(admin_headers) -> None:
    client = TestClient(create_app())
    response = client.put("/v1/collaboration/consent", json={}, headers={**admin_headers, "origin": "https://evil.example"})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "browser_write_denied"


def test_same_origin_browser_write_uses_ephemeral_session_csrf(admin_headers) -> None:
    client = TestClient(create_app(), base_url="http://testserver")
    session = client.get("/v1/session", headers=admin_headers)
    assert session.status_code == 200
    csrf = session.json()["csrf_token"]
    payload = {
        "sharing_enabled": True,
        "research_enabled": False,
        "hazards": {"wildfire": True, "earthquake": True, "flood": True, "landslide": True},
        "policy_version": "collab-demo-v1",
        "updated_at": "2026-08-13T20:00:00Z",
    }
    response = client.put(
        "/v1/collaboration/consent",
        json=payload,
        headers={**admin_headers, "origin": "http://testserver", "x-csrf-token": csrf},
    )
    assert response.status_code == 200
    assert response.json()["accepted"] is True
