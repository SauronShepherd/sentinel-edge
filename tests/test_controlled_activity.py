from sentinel_edge.domain.models import IncidentCommandKind

from tests.test_incident_commands_and_relations import current_by_hazard, seeded_client


def test_controlled_activity_is_recorded_and_duplicate_suppressed(operator_headers, viewer_headers) -> None:
    client = seeded_client(operator_headers)
    current = current_by_hazard(client, viewer_headers)["wildfire"]
    request = {
        "command": IncidentCommandKind.CONTROL.value,
        "expected_version": current["version"],
        "reason": "authorized vegetation clearing near the camera sector",
        "idempotency_key": "wildfire-control-activity-1",
    }
    first = client.post("/v1/incidents/wildfire/commands", json=request, headers=operator_headers)
    assert first.status_code == 200
    assert first.json()["version"] == current["version"] + 1
    assert first.json()["state"] == current["state"]
    assert "control" in first.json()["labels"]
    assert "controlled_activity_recorded" in first.json()["reason_codes"]

    retry = client.post("/v1/incidents/wildfire/commands", json=request, headers=operator_headers)
    assert retry.status_code == 200
    assert retry.json()["version"] == first.json()["version"]
    assert retry.json()["labels"] == first.json()["labels"]
