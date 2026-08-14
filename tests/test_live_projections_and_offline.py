from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from sentinel_edge.gateway import create_app
from sentinel_edge.scenario import load_scenario


def _run(client: TestClient, headers: dict[str, str]) -> None:
    response = client.post(
        "/v1/scenarios/run",
        json=load_scenario("fixtures/scenarios/simultaneous-event.json"),
        headers=headers,
    )
    assert response.status_code == 200


def test_authenticated_projection_has_cursor_version_signature_and_etag(
    viewer_headers: dict[str, str], operator_headers: dict[str, str]
) -> None:
    client = TestClient(create_app())
    _run(client, operator_headers)
    unauth = client.get("/v1/projections/incidents")
    assert unauth.status_code == 401
    response = client.get("/v1/projections/incidents", headers=viewer_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["cursor"]["stream_epoch"]
    assert payload["cursor"]["authority_position"] >= 4
    assert payload["cursor"]["projection_version"] >= 1
    assert len(payload["cursor"]["scope_sha256"]) == 64
    assert payload["projection_lag"] == 0
    assert payload["aggregate_versions"]
    assert all(payload["aggregate_versions"].values())
    assert "causation_command_ids" in payload
    assert payload["payload_sha256"]
    assert payload["authentication_tag"]
    assert response.headers["x-projection-authenticated"] == "hmac-sha256"
    satisfied = client.get("/v1/projections/incidents?min_aggregate_version=1", headers=viewer_headers)
    assert satisfied.status_code == 200
    assert satisfied.headers["x-projection-consistency"] == "satisfied"
    pending = client.get("/v1/projections/incidents?min_aggregate_version=999999", headers=viewer_headers)
    assert pending.status_code == 202
    assert pending.json()["consistency"] == "pending"
    cached = client.get(
        "/v1/projections/incidents",
        headers={**viewer_headers, "If-None-Match": response.headers["etag"]},
    )
    assert cached.status_code == 304


def test_stream_gap_and_epoch_change_force_rest_resynchronization(
    viewer_headers: dict[str, str], operator_headers: dict[str, str], admin_headers: dict[str, str]
) -> None:
    client = TestClient(create_app())
    _run(client, operator_headers)
    current = client.get("/v1/projections/incidents", headers=viewer_headers).json()
    cursor = client.get("/v1/projections/incidents", headers=viewer_headers).headers["x-projection-cursor"]
    contiguous = client.get(
        "/v1/projections/incidents/stream",
        headers={**viewer_headers, "Last-Event-ID": cursor},
    )
    assert "event: projection" in contiguous.text
    invalid = client.get(
        "/v1/projections/incidents/stream",
        headers={**viewer_headers, "Last-Event-ID": "invalid"},
    )
    assert "event: resync_required" in invalid.text
    assert "/v1/projections/incidents" in invalid.text
    old_epoch = current["cursor"]["stream_epoch"]
    rebuilt = client.post("/v1/projections/incidents/rebuild", headers=admin_headers)
    assert rebuilt.status_code == 200
    assert rebuilt.json()["stream_epoch"] != old_epoch
    stale = client.get(
        "/v1/projections/incidents/stream",
        headers={**viewer_headers, "Last-Event-ID": cursor},
    )
    assert "event: resync_required" in stale.text


def test_offline_command_is_minimal_reauthorized_and_returns_current_projection(
    operator_headers: dict[str, str]
) -> None:
    client = TestClient(create_app())
    _run(client, operator_headers)
    prepared = client.post(
        "/v1/offline/incidents/earthquake/prepare",
        json={"action": "acknowledge", "idempotency_key": "offline-ack-1"},
        headers=operator_headers,
    )
    assert prepared.status_code == 200
    ticket = prepared.json()["ticket"]
    serialized = str(ticket).lower()
    assert "evidence" not in serialized and "secret" not in serialized
    assert ticket["base_incident_version"] >= 1
    reconciled = client.post(
        "/v1/offline/commands/reconcile",
        json=ticket,
        headers=operator_headers,
    )
    assert reconciled.status_code == 200
    body = reconciled.json()
    assert body["receipt"]["status"] == "committed"
    assert body["projection"]["command_ids"] == [body["receipt"]["command_id"]]
    replay = client.post(
        "/v1/offline/commands/reconcile",
        json=ticket,
        headers=operator_headers,
    )
    assert replay.status_code == 200
    assert replay.json()["receipt"]["command_id"] == body["receipt"]["command_id"]


def test_offline_command_rejects_tamper_wrong_principal_stale_base_and_expiry(
    operator_headers: dict[str, str], admin_headers: dict[str, str]
) -> None:
    client = TestClient(create_app())
    _run(client, operator_headers)
    prepared = client.post(
        "/v1/offline/incidents/flood/prepare",
        json={
            "action": "snooze",
            "idempotency_key": "offline-snooze-1",
            "until": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        },
        headers=operator_headers,
    ).json()["ticket"]

    tampered = dict(prepared)
    tampered["idempotency_key"] = "substituted"
    assert client.post("/v1/offline/commands/reconcile", json=tampered, headers=operator_headers).status_code == 409
    assert client.post("/v1/offline/commands/reconcile", json=prepared, headers=admin_headers).status_code == 409

    # Change authoritative incident version before replaying the original ticket.
    changed = load_scenario("fixtures/scenarios/simultaneous-event.json")
    changed["scenario_id"] = "simultaneous-event-second-epoch"
    for observation in changed["observations"]:
        observation["boot_id"] = "fixture-boot-2"
        observation["sequence"] += 10
    changed_run = client.post("/v1/scenarios/run", json=changed, headers=operator_headers)
    assert changed_run.status_code == 200
    stale = client.post("/v1/offline/commands/reconcile", json=prepared, headers=operator_headers)
    assert stale.status_code == 409
    assert "stale" in stale.json()["detail"]["message"]

    fresh = client.post(
        "/v1/offline/incidents/earthquake/prepare",
        json={"action": "acknowledge", "idempotency_key": "offline-expired-1"},
        headers=operator_headers,
    ).json()["ticket"]
    fresh["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    expired = client.post("/v1/offline/commands/reconcile", json=fresh, headers=operator_headers)
    assert expired.status_code == 409
    # Altering expiry invalidates the authenticated ticket before it can be treated as a valid expired command.
    assert expired.json()["detail"]["code"] == "offline_command_rejected"


def test_command_receipt_survives_restart_and_remains_separate_from_projection(
    tmp_path, operator_headers: dict[str, str], viewer_headers: dict[str, str]
) -> None:
    from sentinel_edge.scenario import DeterministicScenarioEngine

    state_dir = tmp_path / "state"
    engine = DeterministicScenarioEngine(state_dir=state_dir)
    first_client = TestClient(create_app(engine))
    _run(first_client, operator_headers)
    response = first_client.post(
        "/v1/incidents/earthquake/acknowledge",
        json={"idempotency_key": "durable-receipt-1"},
        headers=operator_headers,
    )
    assert response.status_code == 200
    receipt = response.json()["receipt"]

    restarted = DeterministicScenarioEngine(state_dir=state_dir)
    second_client = TestClient(create_app(restarted))
    receipts = second_client.get("/v1/commands", headers=viewer_headers).json()
    assert receipts[-1]["command_id"] == receipt["command_id"]
    assert receipts[-1]["status"] == "committed"
    projection = second_client.get("/v1/projections/incidents", headers=viewer_headers).json()
    assert receipt["command_id"] in projection["command_ids"]
    assert projection["rebuild_state"] == "ready"
