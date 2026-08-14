from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from sentinel_edge.gateway import create_app
from sentinel_edge.scenario import load_scenario


def test_admin_disposition_api_restricts_immediately_and_operator_cannot_govern(
    admin_headers: dict[str, str], operator_headers: dict[str, str], viewer_headers: dict[str, str]
) -> None:
    client = TestClient(create_app())
    assert client.post(
        "/v1/scenarios/run", json=load_scenario("fixtures/scenarios/simultaneous-event.json"), headers=operator_headers
    ).status_code == 200
    evidence = client.post(
        "/v1/incidents/wildfire/evidence",
        headers=operator_headers,
        json={
            "source_id": "privacy-api-camera",
            "source_standing": "first_party",
            "media_integrity": "original_verified",
            "extraction_confidence_state": "verified",
            "extraction_confidence": 1.0,
            "freshness_state": "healthy",
            "claim_text": "subject-linked frame",
            "content_sha256": hashlib.sha256(b"not-retained-api-fixture").hexdigest(),
            "origin_key": "privacy-api-origin",
            "retention_state": "metadata_only",
            "parser_state": "sandboxed",
            "rights_basis": "consent",
            "rights_mode": "derived_only",
            "modality": "image",
            "subject_ref": "subject-api-1",
            "processing_basis": "consent",
        },
    )
    assert evidence.status_code == 200
    evidence_id = evidence.json()["evidence"]["evidence_id"]
    denied = client.post(
        "/v1/disposition/requests",
        headers=operator_headers,
        json={
            "action": "erase",
            "evidence_ids": [evidence_id],
            "subject_ref": "subject-api-1",
            "subject_basis": "consent",
            "reason": "user request",
            "deadline": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        },
    )
    assert denied.status_code == 403
    created = client.post(
        "/v1/disposition/requests",
        headers=admin_headers,
        json={
            "action": "erase",
            "evidence_ids": [evidence_id],
            "subject_ref": "subject-api-1",
            "subject_basis": "consent",
            "reason": "user request",
            "deadline": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        },
    )
    assert created.status_code == 200
    listed = client.get("/v1/incidents/wildfire/evidence", headers=viewer_headers).json()
    selected = next(item for item in listed if item["evidence_id"] == evidence_id)
    assert selected["disposition_restricted"] is True
    assert selected["claim_text"] == "[RESTRICTED_PENDING_DISPOSITION]"
    closed = client.post(
        f"/v1/disposition/requests/{created.json()['request_id']}/close",
        headers=admin_headers,
        json={"now": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()},
    )
    assert closed.status_code == 200
    assert closed.json()["report"]["status"] == "completed"
