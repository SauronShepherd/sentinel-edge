from __future__ import annotations

import argparse
import json
import tempfile
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

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
from sentinel_edge.operations import DecommissionManager, NetworkExposureEvidence
from sentinel_edge.privacy import DispositionAction, DispositionNodeKind
from sentinel_edge.projections import ProjectionService
from sentinel_edge.review import AfterEventReviewBuilder
from sentinel_edge.scenario import DeterministicScenarioEngine, load_scenario
from sentinel_edge.security import canonical_json_bytes, sha256_bytes
from sentinel_edge.storage import ArtifactPolicy, StateBackupManager


def seed(root: Path, state: Path, at: datetime) -> None:
    engine = DeterministicScenarioEngine(state_dir=state)
    result = engine.run(load_scenario(root / "fixtures/scenarios/simultaneous-event.json"))
    incident = next(item for item in engine.incidents.current() if item.hazard is HazardKind.WILDFIRE)
    ref = engine.artifacts.put_bytes(
        b"v0.15 authority-watermark closure evidence",
        media_type="image/png",
        policy=ArtifactPolicy.incident_evidence(),
    )
    evidence = engine.evidence.ingest(EvidenceItem(
        evidence_id=UUID("01500000-0000-5000-8000-000000000001"),
        incident_id=incident.incident_id,
        hazard=HazardKind.WILDFIRE,
        source_id="camera-v015",
        source_standing=SourceStanding.FIRST_PARTY,
        media_integrity=MediaIntegrityState.ORIGINAL_VERIFIED,
        extraction_confidence_state=ExtractionConfidenceState.VERIFIED,
        extraction_confidence=1.0,
        freshness_state=HealthState.HEALTHY,
        claim_text="Deterministic v0.15 evidence",
        content_sha256=ref.sha256,
        origin_key="v015-frame-1",
        retention_state=EvidenceRetentionState.RETAINED,
        parser_state=ParserIsolationState.SANDBOXED,
        rights_basis="device-owner",
        modality="image",
        received_at=at,
    ))
    return engine, result, evidence


def build(root: Path) -> dict:
    at = datetime(2026, 8, 3, 7, 0, tzinfo=timezone.utc)
    with tempfile.TemporaryDirectory(prefix="sentinel-v015-evidence-") as temporary:
        work = Path(temporary)
        state = work / "state"
        engine, scenario_result, evidence = seed(root, state, at)
        expected = engine.incidents.authority_watermark().model_dump(mode="json")
        projections = ProjectionService(engine.incidents)
        projection = projections.snapshot(generated_at=at)
        aer = AfterEventReviewBuilder().build(engine, scenario_result)

        backup = work / "state.zip"
        backup_manager = StateBackupManager()
        backup_manager.create(state, backup, created_at=at)
        backup_verification = backup_manager.verify(backup)
        restore = backup_manager.restore(backup, work / "restored")

        export_path = work / "evidence.zip"
        export_manifest = engine.exports.create(
            export_path,
            selections=(EvidenceExportSelection(
                evidence_id=evidence.evidence_id,
                classification=ArtifactClassification.RESTRICTED,
            ),),
            created_at=at + timedelta(minutes=1),
        )
        export_verification = engine.exports.verify(export_path)
        resync_payload = json.loads(next(
            line[6:] for line in projections.sse("resync_required", projection).splitlines()
            if line.startswith("data: ")
        ))

        recipient = engine.disposition.register_node(
            evidence_id=evidence.evidence_id,
            kind=DispositionNodeKind.EXTERNAL_RECIPIENT,
            target_ref="recipient-copy:v015",
            external_recipient="processor@example.invalid",
        )
        request = engine.disposition.create_request(
            action=DispositionAction.ERASE,
            evidence_ids=(evidence.evidence_id,),
            subject_ref="subject-v015",
            subject_basis="approved-erasure",
            actor="privacy-admin",
            reason="v0.15 reconciliation proof",
            deadline=at + timedelta(hours=1),
            created_at=at,
        )
        first = engine.disposition.reconcile_external_recipients(
            request.request_id,
            sender=lambda _: (False, "transport_timeout"),
            actor="privacy-worker",
            now=at + timedelta(minutes=1),
            retry_delay_seconds=300,
        )
        restarted = DeterministicScenarioEngine(state_dir=state)
        not_due = restarted.disposition.reconcile_external_recipients(
            request.request_id,
            sender=lambda _: (False, "must_not_be_called"),
            actor="privacy-worker",
            now=at + timedelta(minutes=2),
            retry_delay_seconds=300,
        )
        success = restarted.disposition.reconcile_external_recipients(
            request.request_id,
            sender=lambda node: (node.node_id == recipient.node_id, "remote-deletion-receipt-v015"),
            actor="privacy-worker",
            now=at + timedelta(minutes=7),
            retry_delay_seconds=300,
        )

        network_engine = DeterministicScenarioEngine()
        network_engine.run(load_scenario(root / "fixtures/scenarios/simultaneous-event.json"))
        network_evidence = NetworkExposureEvidence.create(
            observed_at=at,
            observer="field-operator",
            listening_endpoints=("127.0.0.1:8000",),
            permitted_loopback_endpoints=("127.0.0.1:8000",),
            firewall_default_deny=True,
            ingress_rules_removed=True,
            service_bindings_removed=True,
            external_probe_results={"198.51.100.2:8000": "refused"},
        )
        decommission = DecommissionManager(network_engine).execute(
            actor="field-operator",
            reason="v0.15 controlled retirement",
            network_exposure_evidence=network_evidence,
            now=at,
        )

        surfaces = {
            "projection": projection.authority_watermark.model_dump(mode="json"),
            "after_event_review": aer["authority_watermark"],
            "backup": backup_verification["manifest"]["authority_watermark"],
            "restore": restore["authority_watermark"],
            "export": export_manifest.authority_watermark_record.model_dump(mode="json"),
            "export_verification": export_verification["manifest"]["authority_watermark_record"],
            "client_resynchronization": resync_payload["authority_watermark"],
        }
        base = {
            "schema": "sentinel-edge-v015-evidence/1.0",
            "generated_at": at.isoformat(),
            "authority": {
                "expected": expected,
                "surfaces": surfaces,
                "all_equal": all(value == expected for value in surfaces.values()),
                "backup_verified": backup_verification["valid"],
                "export_verified": export_verification["valid"],
                "aer_verified": AfterEventReviewBuilder().verify(aer),
                "projection_verified": projections.verify(projection),
            },
            "external_recipient": {
                "first": first.model_dump(mode="json"),
                "restart_not_due": not_due.model_dump(mode="json"),
                "success": success.model_dump(mode="json"),
                "persisted_attempt_count": len(restarted.disposition.external_reconciliation_attempts(request.request_id)),
            },
            "network_removal": decommission.model_dump(mode="json"),
            "limitations": [
                "External-recipient closure covers registered recipients only.",
                "Network evidence is application/deployment evidence, not host forensic proof.",
                "No target, field, secure-erasure or release-admission claim is made.",
            ],
        }
        return {**base, "receipt_sha256": sha256_bytes(canonical_json_bytes(base))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = build(Path(args.root).resolve())
    Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
