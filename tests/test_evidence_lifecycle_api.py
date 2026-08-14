from __future__ import annotations

import base64
import hashlib
import io
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from PIL import Image

from sentinel_edge.gateway import create_app
from sentinel_edge.scenario import load_scenario


def seed(client: TestClient, headers: dict[str, str]) -> None:
    response = client.post(
        "/v1/scenarios/run", json=load_scenario("fixtures/scenarios/simultaneous-event.json"), headers=headers
    )
    assert response.status_code == 200


def test_admin_governs_lifecycle_operator_cannot_delete(
    operator_headers: dict[str, str], admin_headers: dict[str, str], viewer_headers: dict[str, str]
) -> None:
    client = TestClient(create_app())
    seed(client, operator_headers)
    received = datetime.now(timezone.utc)
    created = client.post(
        "/v1/incidents/wildfire/evidence",
        headers=operator_headers,
        json={
            "source_id": "camera-review",
            "source_standing": "first_party",
            "media_integrity": "original_verified",
            "extraction_confidence_state": "verified",
            "extraction_confidence": 1.0,
            "freshness_state": "healthy",
            "claim_text": "Smoke visible",
            "content_sha256": hashlib.sha256(b"api-media").hexdigest(),
            "origin_key": "frame-api-1",
            "retention_state": "retained",
            "parser_state": "sandboxed",
            "rights_basis": "temporary-license",
            "rights_expires_at": (received + timedelta(minutes=5)).isoformat(),
            "modality": "image",
        },
    )
    assert created.status_code == 200
    evidence_id = created.json()["evidence"]["evidence_id"]
    denied = client.post(
        f"/v1/incidents/wildfire/evidence/{evidence_id}/delete",
        headers=operator_headers,
        json={"expected_version": 1, "reason": "operator must not erase"},
    )
    assert denied.status_code == 403
    redacted = client.post(
        f"/v1/incidents/wildfire/evidence/{evidence_id}/redact",
        headers=admin_headers,
        json={"expected_version": 1, "reason": "privacy minimization", "redaction_profile_id": "metadata-v1"},
    )
    assert redacted.status_code == 200
    assert redacted.json()["projection"]["state"] == "redacted"
    lifecycle = client.get("/v1/incidents/wildfire/evidence-lifecycle", headers=viewer_headers)
    assert lifecycle.status_code == 200
    assert [event["action"] for event in lifecycle.json()["events"]] == ["register", "redact"]


def test_rights_expiry_and_parser_api_are_audited(
    operator_headers: dict[str, str], admin_headers: dict[str, str], viewer_headers: dict[str, str]
) -> None:
    client = TestClient(create_app())
    seed(client, operator_headers)
    now = datetime.now(timezone.utc)
    created = client.post(
        "/v1/incidents/flood/evidence",
        headers=operator_headers,
        json={
            "source_id": "licensed-report",
            "source_standing": "authoritative",
            "media_integrity": "not_applicable",
            "extraction_confidence_state": "not_applicable",
            "freshness_state": "healthy",
            "claim_text": "River level report",
            "content_sha256": hashlib.sha256(b"report").hexdigest(),
            "origin_key": "report-1",
            "retention_state": "retained",
            "parser_state": "not_required",
            "rights_basis": "time-bounded-license",
            "rights_expires_at": (now + timedelta(minutes=1)).isoformat(),
            "modality": "document",
        },
    )
    assert created.status_code == 200
    expired = client.post(
        "/v1/evidence/enforce-rights-expiry",
        headers=admin_headers,
        json={"now": (now + timedelta(minutes=2)).isoformat()},
    )
    assert expired.status_code == 200
    assert expired.json()["count"] == 1

    image = Image.new("RGB", (8, 8), "red")
    out = io.BytesIO(); image.save(out, format="JPEG")
    parsed = client.post(
        "/v1/media/parse",
        headers=operator_headers,
        json={
            "media_type": "image/jpeg",
            "data_base64": base64.b64encode(out.getvalue()).decode(),
            "persist_sanitized": True,
        },
    )
    assert parsed.status_code == 200
    assert parsed.json()["report"]["status"] == "completed"
    assert parsed.json()["artifact"]["media_type"] == "image/png"
    assert parsed.json()["authority_effect"] == "none_until_evidence_is_explicitly_ingested"
    reports = client.get("/v1/media/parse-reports", headers=viewer_headers)
    assert reports.status_code == 200
    assert len(reports.json()) == 1
    authority_kinds = [item["kind"] for item in client.get("/v1/authority-journal", headers=viewer_headers).json()]
    assert "media_parse" in authority_kinds
