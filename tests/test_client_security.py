from fastapi.testclient import TestClient

from sentinel_edge.gateway import create_app


def test_client_is_semantic_and_service_worker_never_caches_api_or_credentials(
    viewer_headers: dict[str, str],
) -> None:
    client = TestClient(create_app())
    page = client.get("/client")
    assert page.status_code == 200
    assert "<main>" in page.text
    assert 'aria-live="polite"' in page.text
    assert 'label for="token"' in page.text
    assert "not an official warning service" in page.text.lower()
    assert "frame-ancestors 'none'" in page.headers["content-security-policy"]

    script = client.get("/client/app.js").text
    assert "localStorage" not in script
    assert "sessionStorage" not in script
    assert "cache: 'no-store'" in script
    assert "resync_required" in script
    assert "reason_codes" in script
    assert "<strong>Why:</strong>" in script
    assert "<strong>Freshness:</strong>" in script
    assert "unknown" in script
    assert "Scheduler activity:" in page.text
    assert 'id="system-health"' in page.text
    assert 'id="results"' in page.text
    assert 'id="system-health"' in page.text.split('id="results"', 1)[0]
    assert "serving hazard projections" in script
    assert "idle" in script
    assert "await loadIncidents()" in script
    assert "Last-Event-ID" in script
    assert "const HAZARDS = ['wildfire', 'earthquake', 'flood', 'landslide'];" in script
    assert "HAZARDS.map" in script
    assert script.count("class=\"hazard-card\"") >= 1

    worker = client.get("/client/service-worker.js").text
    assert "/v1" not in worker
    assert "Authorization" not in worker
    assert "ALLOWLIST" in worker

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
    assert "fetch('/v1/" in script
    assert "credentials: 'omit'" in script
