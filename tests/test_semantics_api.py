from datetime import datetime, timezone

from fastapi.testclient import TestClient

from sentinel_edge.gateway import create_app


def test_time_measurement_and_geospatial_contract_endpoints(viewer_headers: dict[str, str], operator_headers: dict[str, str]) -> None:
    client = TestClient(create_app())
    time_state = client.get("/v1/time", headers=viewer_headers)
    assert time_state.status_code == 200
    assert time_state.json()["state"] == "trusted"

    now = datetime(2026, 8, 2, 18, 0, tzinfo=timezone.utc).isoformat()
    observation = {
        "source_id": "gauge-1", "hazard": "flood", "source_mode": "fixture", "sequence": 1,
        "observed_at": now, "received_at": now,
        "values": {"water_level_m": 1.0, "rate_of_rise_m_per_h": 0.2},
        "units": {"water_level_m": "m", "rate_of_rise_m_per_h": "m/h"},
        "measurement_references": {"water_level_m": "datum:1", "rate_of_rise_m_per_h": "datum:1"},
    }
    measured = client.post("/v1/measurements/validate", json=observation, headers=viewer_headers)
    assert measured.status_code == 200
    assert measured.json()["valid"] is True

    geometry = client.post(
        "/v1/geospatial/validate",
        json={"geometry": {"type": "Point", "coordinates": [-3.7, 40.4]}},
        headers=viewer_headers,
    )
    assert geometry.status_code == 200
    assert geometry.json()["decision"] == "valid"

    update = client.post(
        "/v1/time/evaluate",
        json={
            "source_id": "ntp", "origin": "ntp", "authenticated": False,
            "observed_utc": now, "observed_monotonic_ns": 2_000_000_000,
            "uncertainty_ms": 20, "age_ms": 0, "stratum": 2,
            "reference_id": "pool", "continuity_id": "boot-1", "clock_epoch": 0,
            "certificate_bootstrap_valid": True,
        },
        headers=operator_headers,
    )
    assert update.status_code == 403
