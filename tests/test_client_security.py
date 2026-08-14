from fastapi.testclient import TestClient

from sentinel_edge.gateway import create_app


def test_client_is_semantic_and_service_worker_never_caches_api_or_credentials(
    viewer_headers: dict[str, str],
) -> None:
    client = TestClient(create_app())
    page = client.get("/client")
    assert page.status_code == 200
    assert "<main" in page.text
    assert 'aria-live="polite"' in page.text
    assert 'id="token"' in page.text
    assert "not an official emergency-warning system" in page.text.lower()
    assert "arm64 emulated demonstration environment" in page.text.lower()
    assert "frame-ancestors 'none'" in page.headers["content-security-policy"]

    script = client.get("/client/app.js").text
    assert "localStorage" not in script
    assert "sessionStorage" not in script
    assert "indexedDB" not in script
    assert "cache:'no-store'" in script or "cache: 'no-store'" in script
    assert "credentials:'omit'" in script or "credentials: 'omit'" in script
    assert "reason_codes" in script
    assert "Component 4" in script
    assert all(hazard in script for hazard in ("wildfire", "earthquake", "flood", "landslide"))
    assert "Running" in script and "Queued" in script and "Sleeping" in script and "Deferred" in script
    assert "/v1/release-info" in script
    assert "/v1/projections/incidents" in script
    assert "/v1/runtime" in script
    assert "/v1/benchmark/summary" in script
    assert "/v1/judge-proof" in script

    worker = client.get("/client/service-worker.js").text
    assert "/v1" not in worker
    assert "Authorization" not in worker
    assert "ALLOWLIST" in worker
    assert "/client/styles.css" in worker

    protected = client.get("/v1/incidents", headers=viewer_headers)
    assert protected.status_code == 200
    assert protected.headers["cache-control"] == "no-store, private"
    assert protected.headers["pragma"] == "no-cache"


def test_client_has_no_persistence_or_backend_boundary_access() -> None:
    client = TestClient(create_app())
    page = client.get("/client").text
    script = client.get("/client/app.js").text
    client_surface = page + script
    forbidden = ("sqlite", "indexeddb", "localStorage", "sessionStorage", "internal-transport", "database")
    assert [marker for marker in forbidden if marker.lower() in client_surface.lower()] == []
    assert "fetch(path" in script
    assert "credentials:'omit'" in script or "credentials: 'omit'" in script
