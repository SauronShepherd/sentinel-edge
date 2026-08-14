from __future__ import annotations

import base64
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from sentinel_edge.domain.models import (
    EvidenceItem,
    EvidenceRetentionState,
    ExtractionConfidenceState,
    HazardKind,
    HealthState,
    MediaIntegrityState,
    ParserIsolationState,
    SourceStanding,
)
from sentinel_edge.exports import ArtifactClassification, EvidenceExportSelection
from sentinel_edge.gateway import create_app
from sentinel_edge.scenario import DeterministicScenarioEngine, load_scenario


def test_export_api_requires_governance_and_returns_opaque_artifact(
    tmp_path: Path,
    admin_headers: dict[str, str],
    operator_headers: dict[str, str],
    viewer_headers: dict[str, str],
) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    engine.run(load_scenario("fixtures/scenarios/simultaneous-event.json"))
    incident = next(item for item in engine.incidents.current() if item.hazard is HazardKind.WILDFIRE)
    evidence = engine.evidence.ingest(EvidenceItem(
        incident_id=incident.incident_id,
        hazard=HazardKind.WILDFIRE,
        source_id="community-report-1",
        source_standing=SourceStanding.COMMUNITY,
        media_integrity=MediaIntegrityState.NOT_APPLICABLE,
        extraction_confidence_state=ExtractionConfidenceState.VERIFIED,
        extraction_confidence=1.0,
        freshness_state=HealthState.HEALTHY,
        claim_text="Visible smoke report",
        content_sha256="a" * 64,
        origin_key="report-1",
        retention_state=EvidenceRetentionState.METADATA_ONLY,
        parser_state=ParserIsolationState.NOT_REQUIRED,
        modality="text",
    ))
    client = TestClient(create_app(engine))
    payload = {
        "selections": [{
            "evidence_id": str(evidence.evidence_id),
            "classification": ArtifactClassification.RESTRICTED.value,
            "include_content": False,
            "redaction_profile": "restricted-export-v1",
        }],
        "derivatives": [],
    }
    denied = client.post("/v1/exports/evidence", json=payload, headers=operator_headers)
    assert denied.status_code == 403

    created = client.post("/v1/exports/evidence", json=payload, headers=admin_headers)
    assert created.status_code == 200
    body = created.json()
    assert body["path_disclosed"] is False
    assert set(body["artifact"]) == {"sha256", "bytes", "media_type"}
    assert body["manifest"]["secret_values_persisted"] is False

    catalog = client.get("/v1/artifacts", headers=admin_headers)
    assert catalog.status_code == 200
    assert catalog.json()["records"]
    assert all("relative_path" not in record for record in catalog.json()["records"])

    guessed = client.get("/v1/artifacts/" + ("f" * 64), headers=viewer_headers)
    assert guessed.status_code == 404

    raw_path = client.post(
        "/v1/exports/evidence",
        json={**payload, "path": "C:/sentinel-edge/private/artifacts/secret.bin"},
        headers=admin_headers,
    )
    assert raw_path.status_code == 422

    local_zip = tmp_path / "local-export.zip"
    engine.exports.create(
        local_zip,
        selections=(EvidenceExportSelection(
            evidence_id=evidence.evidence_id,
            classification=ArtifactClassification.INTERNAL,
        ),),
    )
    verified = client.post(
        "/v1/exports/verify",
        json={"data_base64": base64.b64encode(local_zip.read_bytes()).decode("ascii")},
        headers=viewer_headers,
    )
    assert verified.status_code == 200
    assert verified.json()["valid"] is True
    assert verified.json()["verified_by"] == "development-viewer"
