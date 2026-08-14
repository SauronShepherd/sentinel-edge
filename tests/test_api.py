from fastapi.testclient import TestClient
from sentinel_edge.gateway import create_app


def test_health_and_invalid_scenario_errors_are_structured(operator_headers: dict[str, str]) -> None:
    client = TestClient(create_app())
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["components"] == 6
    assert health.json()["authentication"]["enabled"] is True
    unauthenticated = client.get("/v1/incidents")
    assert unauthenticated.status_code == 401
    error = client.post("/v1/scenarios/run", json={}, headers=operator_headers)
    assert error.status_code == 422
    assert error.json()["detail"]["code"] == "invalid_scenario"


def test_supported_operations_are_versioned_and_in_openapi() -> None:
    app = create_app()
    documented = app.openapi()["paths"]
    versioned = {
        route.path
        for route in app.routes
        if getattr(route, "include_in_schema", True)
        and route.path not in {"/", "/ready", "/health"}
    }
    assert versioned
    assert all(path.startswith("/v1/") for path in versioned)
    assert versioned <= set(documented)
    assert any("get" in documented[path] for path in versioned)
    assert any("post" in documented[path] for path in versioned)
