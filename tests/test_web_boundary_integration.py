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
