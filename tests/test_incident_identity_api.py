from datetime import datetime, timezone

from fastapi.testclient import TestClient

from sentinel_edge.gateway import create_app


def test_identity_api_deduplicates_repeat_candidate(
    operator_headers: dict[str, str], viewer_headers: dict[str, str]
) -> None:
    client = TestClient(create_app())
    payload = {
        "hazard": "flood",
        "observed_at": datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc).isoformat(),
        "latitude": 40.4,
        "longitude": -3.7,
        "horizontal_uncertainty_m": 25,
        "temporal_window_seconds": 300,
        "spatial_window_m": 1000,
        "source_id": "gauge-1",
        "source_event_id": "rise-42",
    }
    first = client.post("/v1/incidents/identity/resolve", json=payload, headers=operator_headers)
    second = client.post("/v1/incidents/identity/resolve", json=payload, headers=operator_headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["decision"]["outcome"] == "new"
    assert second.json()["decision"]["outcome"] == "duplicate"
    assert second.json()["decision"]["incident_id"] == first.json()["decision"]["incident_id"]
    decisions = client.get("/v1/incidents/identity/decisions", headers=viewer_headers)
    assert decisions.status_code == 200
    assert len(decisions.json()) == 2
