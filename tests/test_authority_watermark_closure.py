from __future__ import annotations

import json
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

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
from sentinel_edge.storage.restore_authorization import RestoreAuthorization
from sentinel_edge.exports import ArtifactClassification, EvidenceExportSelection
from sentinel_edge.operations import DecommissionManager, NetworkExposureEvidence
from sentinel_edge.privacy import DispositionAction, DispositionNodeKind, RecipientReconciliationState
from sentinel_edge.projections import ProjectionService
from sentinel_edge.review import AfterEventReviewBuilder
from sentinel_edge.scenario import DeterministicScenarioEngine, load_scenario
from sentinel_edge.storage import ArtifactPolicy, StateBackupManager


def _seed(tmp_path: Path):
    state = tmp_path / "state"
    engine = DeterministicScenarioEngine(state_dir=state)
    result = engine.run(load_scenario("fixtures/scenarios/simultaneous-event.json"))
    incident = next(item for item in engine.incidents.current() if item.hazard is HazardKind.WILDFIRE)
    artifact = engine.artifacts.put_bytes(
        b"watermark-closure-evidence", media_type="image/png", policy=ArtifactPolicy.incident_evidence()
    )
    evidence = engine.evidence.ingest(EvidenceItem(
        incident_id=incident.incident_id,
        hazard=HazardKind.WILDFIRE,
        source_id="camera-watermark",
        source_standing=SourceStanding.FIRST_PARTY,
        media_integrity=MediaIntegrityState.ORIGINAL_VERIFIED,
        extraction_confidence_state=ExtractionConfidenceState.VERIFIED,
        extraction_confidence=1.0,
        freshness_state=HealthState.HEALTHY,
        claim_text="Smoke observation",
        content_sha256=artifact.sha256,
        origin_key="watermark-frame-1",
        retention_state=EvidenceRetentionState.RETAINED,
        parser_state=ParserIsolationState.SANDBOXED,
        rights_basis="device-owner",
        modality="image",
    ))
    return state, engine, result, evidence


def test_one_authority_watermark_is_propagated_to_all_derived_surfaces(tmp_path: Path) -> None:
    state, engine, scenario_result, evidence = _seed(tmp_path)
    expected = engine.incidents.authority_watermark().model_dump(mode="json")
    assert expected["valid"] is True

    projection_service = ProjectionService(engine.incidents)
    projection = projection_service.snapshot()
    assert projection.authority_watermark.model_dump(mode="json") == expected
    assert projection.last_applied_authority_position == expected["highest_contiguous_position"]

    review = AfterEventReviewBuilder().build(engine, scenario_result)
    assert review["authority_watermark"] == expected

    backup = tmp_path / "state.zip"
    manager = StateBackupManager()
    manager.create(state, backup, created_at=datetime(2026, 8, 3, 6, 0, tzinfo=timezone.utc))
    verified_backup = manager.verify(backup)
    assert verified_backup["valid"] is True
    assert verified_backup["manifest"]["authority_watermark"] == expected
    restored = manager.restore(backup, tmp_path / "restored", authorization=RestoreAuthorization(
        actor="operator", reason="watermark recovery", target_node="local-node", target_namespace="restored", policy_version="restore-v1"))
    assert restored["authority_watermark"] == expected

    export_path = tmp_path / "evidence.zip"
    manifest = engine.exports.create(
        export_path,
        selections=(EvidenceExportSelection(
            evidence_id=evidence.evidence_id,
            classification=ArtifactClassification.RESTRICTED,
        ),),
        created_at=datetime(2026, 8, 3, 6, 1, tzinfo=timezone.utc),
    )
    assert manifest.authority_watermark_record.model_dump(mode="json") == expected
    assert engine.exports.verify(export_path)["manifest"]["authority_watermark_record"] == expected

    sse = projection_service.sse("resync_required", projection)
    data = json.loads(next(line[6:] for line in sse.splitlines() if line.startswith("data: ")))
    assert data["authority_watermark"] == expected
    assert data["current"]["authority_watermark"] == expected



def test_backup_watermark_tampering_is_bound_to_the_copied_authority_store(tmp_path: Path) -> None:
    state, _, _, _ = _seed(tmp_path)
    manager = StateBackupManager()
    backup = tmp_path / "state.zip"
    manager.create(state, backup, created_at=datetime(2026, 8, 3, 7, 0, tzinfo=timezone.utc))
    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(backup) as source, zipfile.ZipFile(tampered, "w") as target:
        for name in source.namelist():
            data = source.read(name)
            if name == "backup-manifest.json":
                manifest = json.loads(data)
                manifest["authority_watermark"]["accepted_event_count"] += 1
                data = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
            target.writestr(name, data)
    result = manager.verify(tampered)
    assert result["valid"] is False
    assert "authority_watermark_not_bound_to_incident_store" in result["errors"]

def test_external_recipient_reconciliation_is_restart_safe_bounded_and_resumable(tmp_path: Path) -> None:
    state, engine, _, evidence = _seed(tmp_path)
    node = engine.disposition.register_node(
        evidence_id=evidence.evidence_id,
        kind=DispositionNodeKind.EXTERNAL_RECIPIENT,
        target_ref="recipient-copy:case-7",
        external_recipient="processor@example.invalid",
    )
    created = datetime(2026, 8, 3, 6, 0, tzinfo=timezone.utc)
    request = engine.disposition.create_request(
        action=DispositionAction.ERASE,
        evidence_ids=(evidence.evidence_id,),
        subject_ref="subject-7",
        subject_basis="approved-erasure",
        actor="privacy-admin",
        reason="erase recipient copy",
        deadline=created + timedelta(hours=1),
        created_at=created,
    )
    first = engine.disposition.reconcile_external_recipients(
        request.request_id,
        sender=lambda _: (False, "transport_timeout"),
        actor="privacy-worker",
        now=created + timedelta(minutes=1),
        retry_delay_seconds=300,
    )
    assert first.retry_scheduled == 1 and first.complete is False
    assert first.attempts[0].state is RecipientReconciliationState.RETRY_SCHEDULED

    restarted = DeterministicScenarioEngine(state_dir=state)
    not_due = restarted.disposition.reconcile_external_recipients(
        request.request_id,
        sender=lambda _: (_ for _ in ()).throw(AssertionError("sender must not run before retry time")),
        actor="privacy-worker",
        now=created + timedelta(minutes=2),
        retry_delay_seconds=300,
    )
    assert not_due.attempts[0].state is RecipientReconciliationState.NOT_DUE

    successful = restarted.disposition.reconcile_external_recipients(
        request.request_id,
        sender=lambda candidate: (candidate.node_id == node.node_id, "remote-deletion-receipt-7"),
        actor="privacy-worker",
        now=created + timedelta(minutes=7),
        retry_delay_seconds=300,
    )
    assert successful.complete is True
    assert successful.acknowledged == 1
    assert successful.attempts[0].state is RecipientReconciliationState.ACKNOWLEDGED
    assert len(restarted.disposition.external_reconciliation_attempts(request.request_id)) == 2


def test_decommission_carries_observed_network_removal_and_authority_watermark(tmp_path: Path) -> None:
    _, engine, _, _ = _seed(tmp_path)
    observed = datetime(2026, 8, 3, 6, 30, tzinfo=timezone.utc)
    evidence = NetworkExposureEvidence.create(
        observed_at=observed,
        observer="field-operator",
        listening_endpoints=("127.0.0.1:8000",),
        permitted_loopback_endpoints=("127.0.0.1:8000",),
        firewall_default_deny=True,
        ingress_rules_removed=True,
        service_bindings_removed=True,
        external_probe_results={"198.51.100.2:8000": "refused"},
    )
    receipt = DecommissionManager(engine).execute(
        actor="field-operator",
        reason="controlled retirement",
        network_exposure_evidence=evidence,
        now=observed,
    )
    assert receipt.network_exposure_removed is True
    assert receipt.network_exposure_proven is True
    assert receipt.network_exposure_evidence["evidence_sha256"] == evidence.evidence_sha256
    assert receipt.authority_watermark["valid"] is True

    failed = NetworkExposureEvidence.create(
        observed_at=observed,
        observer="field-operator",
        listening_endpoints=("0.0.0.0:8000",),
        firewall_default_deny=False,
        ingress_rules_removed=False,
        service_bindings_removed=False,
        external_probe_results={"198.51.100.2:8000": "reachable"},
    )
    blocked = DecommissionManager(engine).execute(
        actor="field-operator",
        reason="incomplete retirement",
        network_exposure_evidence=failed,
        now=observed,
    )
    assert blocked.state.value == "blocked"
    assert "network_exposure_evidence_failed" in blocked.blockers
