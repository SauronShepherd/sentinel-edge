from fastapi.testclient import TestClient

from sentinel_edge.gateway import create_app
from sentinel_edge.scenario import load_scenario


def test_review_notification_configuration_and_after_event_api_workflows(
    operator_headers: dict[str, str],
    viewer_headers: dict[str, str],
) -> None:
    scenario = load_scenario("fixtures/scenarios/simultaneous-event.json")
    client = TestClient(create_app())
    run = client.post("/v1/scenarios/run", json=scenario, headers=operator_headers)
    assert run.status_code == 200

    notifications = client.get("/v1/notifications", headers=viewer_headers).json()
    assert notifications["delivery_semantics"] == "at_least_once_with_idempotent_consumer"
    assert notifications["metrics"]["pending"] == 4
    first_dispatch = client.post("/v1/notifications/dispatch", headers=operator_headers).json()
    second_dispatch = client.post("/v1/notifications/dispatch", headers=operator_headers).json()
    assert len(first_dispatch["delivered"]) == 4
    assert second_dispatch["delivered"] == []
    assert second_dispatch["consumer_effect_count"] == 4

    acknowledged = client.post(
        "/v1/incidents/earthquake/acknowledge",
        json={"idempotency_key": "ack-eq-1"},
        headers=operator_headers,
    )
    assert acknowledged.status_code == 200
    assert acknowledged.json()["state"]["acknowledged_by"] == "development-operator"
    assert acknowledged.json()["receipt"]["status"] == "committed"
    assert client.get("/v1/authority-journal", headers=viewer_headers).json()[-1]["kind"] == "command"
    assert client.get("/v1/configuration", headers=viewer_headers).json()["active"]["version"] == "0.21.0"

    review_client = TestClient(create_app())
    review = review_client.post("/v1/reviews/after-event", json=scenario, headers=operator_headers)
    assert review.status_code == 200
    assert review.json()["verified"] is True
    assert review.json()["artifact"]["sha256"]
