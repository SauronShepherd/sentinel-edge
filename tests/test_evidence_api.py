from __future__ import annotations

import hashlib

from fastapi.testclient import TestClient

from sentinel_edge.gateway import create_app
from sentinel_edge.scenario import load_scenario


def test_evidence_claim_and_trust_api_keep_dimensions_separate(
    operator_headers: dict[str, str], viewer_headers: dict[str, str]
) -> None:
    client = TestClient(create_app())
    assert client.post(
        "/v1/scenarios/run",
        json=load_scenario("fixtures/scenarios/simultaneous-event.json"),
        headers=operator_headers,
    ).status_code == 200
    content_sha = hashlib.sha256(b"smoke-image").hexdigest()
    evidence = client.post(
        "/v1/incidents/wildfire/evidence",
        headers=operator_headers,
        json={
            "source_id": "camera-review",
            "source_standing": "first_party",
            "media_integrity": "original_verified",
            "extraction_confidence_state": "verified",
            "extraction_confidence": 1.0,
            "freshness_state": "healthy",
            "claim_text": "Smoke plume is visible",
            "content_sha256": content_sha,
            "origin_key": "camera-frame-42",
            "retention_state": "retained",
            "parser_state": "sandboxed",
            "rights_basis": "local-device-owner",
            "modality": "image",
        },
    )
    assert evidence.status_code == 200
    assert evidence.json()["evidence"]["authority_role"] == "operational_source"
    evidence_id = evidence.json()["evidence"]["evidence_id"]
    claim = client.post(
        "/v1/incidents/wildfire/claims",
        headers=operator_headers,
        json={"statement": "A wildfire may be active"},
    )
    assert claim.status_code == 200
    link = client.post(
        f"/v1/claims/{claim.json()['claim_id']}/links",
        headers=operator_headers,
        json={"evidence_id": evidence_id, "relation": "supports"},
    )
    assert link.status_code == 200
    trust = client.get("/v1/incidents/wildfire/trust", headers=viewer_headers).json()
    snapshot = trust["snapshot"]
    assert snapshot["source_standing_counts"] == {"first_party": 1}
    assert snapshot["media_integrity_counts"] == {"original_verified": 1}
    assert snapshot["extraction_confidence_counts"] == {"verified": 1}
    assert snapshot["freshness_counts"] == {"healthy": 1}
    assert snapshot["supporting_links"] == 1
    assert snapshot["summary_band"] == "supported_single_family"
    assert trust["graph_sha256"]
