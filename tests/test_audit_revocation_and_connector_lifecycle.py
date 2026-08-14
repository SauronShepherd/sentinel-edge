from __future__ import annotations

import base64
import time
from typing import Any
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from sentinel_edge.audit import NON_FORENSIC_WORDING
from sentinel_edge.collector import BoundedBackgroundConnector, ConnectorState
from sentinel_edge.domain.models import PrincipalRef, PrincipalRole
from sentinel_edge.gateway import create_app
from sentinel_edge.scenario import DeterministicScenarioEngine, load_scenario
from sentinel_edge.security import (
    AuthManager,
    GrantLifecycleAction,
    KeyLifecycleAction,
    KeyPurpose,
    KeyState,
)


def raw_keys() -> tuple[Ed25519PrivateKey, bytes, bytes]:
    private = Ed25519PrivateKey.generate()
    private_raw = private.private_bytes(
        serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption()
    )
    public_raw = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return private, private_raw, public_raw


def test_signed_audit_checkpoint_detects_truncation_substitution_and_preserves_retired_history(tmp_path) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    engine.run(load_scenario("fixtures/scenarios/simultaneous-event.json"))
    private1, private1_raw, public1 = raw_keys()
    t1 = datetime(2026, 8, 3, 5, 0, tzinfo=timezone.utc)
    engine.key_lifecycle.register(
        identity_id="field-audit",
        generation=1,
        purpose=KeyPurpose.AUDIT_SIGNING,
        public_key_raw=public1,
        policy_version="audit-policy-v1",
        actor="release-admin",
        reason="initial field audit key",
        active_from=t1,
        registered_at=t1,
    )
    entries = engine.incidents.authority_journal()
    checkpoint = engine.audit.create(
        entries=entries,
        authority_epoch_id=engine.incidents.authority_conformance()["epoch_id"],
        signer_identity_id="field-audit",
        signer_generation=1,
        private_key_raw=private1_raw,
        created_at=t1 + timedelta(minutes=1),
    )
    assert checkpoint.non_forensic_wording == NON_FORENSIC_WORDING
    verified = engine.audit.verify(checkpoint, entries=entries)
    assert verified.valid is True
    assert verified.signature.status == "valid_active"

    truncated = engine.audit.verify(checkpoint, entries=entries[:-1])
    assert truncated.valid is False
    assert any("truncated" in item or "invalid" in item for item in truncated.failures)

    altered_first = entries[0].model_copy(update={"payload": {**entries[0].payload, "state": "normal"}})
    substituted = engine.audit.verify(checkpoint, entries=(altered_first, *entries[1:]))
    assert substituted.valid is False
    assert "journal_prefix_substituted" in substituted.failures

    _, private2_raw, public2 = raw_keys()
    engine.key_lifecycle.register(
        identity_id="field-audit",
        generation=2,
        purpose=KeyPurpose.AUDIT_SIGNING,
        public_key_raw=public2,
        policy_version="audit-policy-v2",
        actor="release-admin",
        reason="scheduled rotation",
        active_from=t1 + timedelta(minutes=2),
        registered_at=t1 + timedelta(minutes=2),
    )
    historical = engine.audit.verify(checkpoint, entries=entries)
    assert historical.valid is True
    assert historical.signature.status == "historically_valid_retired"
    assert "retire" in {event.action.value for event in engine.key_lifecycle.events()}
    with pytest.raises(PermissionError, match="not active"):
        engine.audit.create(
            entries=entries,
            authority_epoch_id="authority-epoch-1",
            signer_identity_id="field-audit",
            signer_generation=1,
            private_key_raw=private1_raw,
            created_at=t1 + timedelta(minutes=3),
        )
    assert private1_raw not in (tmp_path / "state" / "key-lifecycle.sqlite3").read_bytes()
    assert private1.sign(b"proof")


def test_policy_revocation_preserves_prior_audit_semantics_but_blocks_new_heads_and_compromise_is_distinct(tmp_path) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    engine.run(load_scenario("fixtures/scenarios/simultaneous-event.json"))
    _, private_raw, public_raw = raw_keys()
    base = datetime(2026, 8, 3, 6, 0, tzinfo=timezone.utc)
    engine.key_lifecycle.register(
        identity_id="audit-policy-key", generation=1, purpose=KeyPurpose.AUDIT_SIGNING,
        public_key_raw=public_raw, policy_version="audit-policy-v1", actor="admin", reason="activate",
        active_from=base, registered_at=base,
    )
    checkpoint = engine.audit.create(
        entries=engine.incidents.authority_journal(), authority_epoch_id="authority-epoch-1",
        signer_identity_id="audit-policy-key", signer_generation=1, private_key_raw=private_raw,
        created_at=base + timedelta(minutes=1),
    )
    engine.key_lifecycle.transition(
        identity_id="audit-policy-key", generation=1, purpose=KeyPurpose.AUDIT_SIGNING,
        action=KeyLifecycleAction.REVOKE_POLICY, actor="admin", reason="policy changed",
        policy_version="audit-policy-v2", effective_at=base + timedelta(minutes=2),
    )
    prior = engine.audit.verify(checkpoint, entries=engine.incidents.authority_journal())
    assert prior.valid is True
    assert prior.signature.status == "historically_valid_before_policy_revocation"
    with pytest.raises(PermissionError):
        engine.audit.create(
            entries=engine.incidents.authority_journal(), authority_epoch_id="authority-epoch-1",
            signer_identity_id="audit-policy-key", signer_generation=1, private_key_raw=private_raw,
            created_at=base + timedelta(minutes=3),
        )

    _, private2_raw, public2 = raw_keys()
    engine.key_lifecycle.register(
        identity_id="audit-compromise-key", generation=1, purpose=KeyPurpose.AUDIT_SIGNING,
        public_key_raw=public2, policy_version="audit-policy-v1", actor="admin", reason="activate",
        active_from=base, registered_at=base,
    )
    checkpoint2 = engine.audit.create(
        entries=engine.incidents.authority_journal(), authority_epoch_id="authority-epoch-1",
        signer_identity_id="audit-compromise-key", signer_generation=1, private_key_raw=private2_raw,
        created_at=base + timedelta(minutes=1),
    )
    engine.key_lifecycle.transition(
        identity_id="audit-compromise-key", generation=1, purpose=KeyPurpose.AUDIT_SIGNING,
        action=KeyLifecycleAction.SUSPECT_COMPROMISE, actor="security", reason="unknown exposure start",
        policy_version="audit-policy-v1", effective_at=base + timedelta(minutes=2),
    )
    compromise = engine.audit.verify(checkpoint2, entries=engine.incidents.authority_journal())
    assert compromise.valid is False
    assert compromise.signature.status == "indeterminate_compromise_interval"
    actions = {event.action.value for event in engine.key_lifecycle.events()}
    assert {"revoke_policy", "suspect_compromise"} <= actions


def test_revoked_source_key_cannot_contribute_new_trusted_evidence(tmp_path) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    private, _, public = raw_keys()
    now = datetime(2026, 8, 3, 7, 0, tzinfo=timezone.utc)
    engine.key_lifecycle.register(
        identity_id="gauge-source-1", generation=1, purpose=KeyPurpose.SOURCE_SIGNING,
        public_key_raw=public, policy_version="source-trust-v1", actor="source-admin", reason="commissioned",
        active_from=now, registered_at=now,
    )
    payload = b'{"source":"gauge-source-1","level_m":1.25}'
    signature = base64.b64encode(private.sign(payload)).decode("ascii")
    before = engine.key_lifecycle.verify(
        identity_id="gauge-source-1", generation=1, purpose=KeyPurpose.SOURCE_SIGNING,
        message=payload, signature_b64=signature, observed_at=now, accepted_at=now + timedelta(seconds=1), historical=False,
    )
    assert before.accepted is True
    engine.key_lifecycle.transition(
        identity_id="gauge-source-1", generation=1, purpose=KeyPurpose.SOURCE_SIGNING,
        action=KeyLifecycleAction.REVOKE_POLICY, actor="source-admin", reason="credential revoked",
        policy_version="source-trust-v2", effective_at=now + timedelta(seconds=2),
    )
    after = engine.key_lifecycle.verify(
        identity_id="gauge-source-1", generation=1, purpose=KeyPurpose.SOURCE_SIGNING,
        message=payload, signature_b64=signature, observed_at=now, accepted_at=now + timedelta(seconds=3), historical=False,
    )
    assert after.accepted is False
    assert after.status == "key_not_accepted_for_new_evidence"
    assert engine.key_lifecycle.records(purpose=KeyPurpose.SOURCE_SIGNING)[0].state is KeyState.REVOKED_POLICY


def test_logout_and_device_revocation_purge_protected_cache_and_queued_authority(tmp_path) -> None:
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    principal = PrincipalRef(principal_id="field-operator", roles=(PrincipalRole.OPERATOR,), session_epoch=4, device_trust_epoch=9)
    issued = datetime(2026, 8, 3, 8, 0, tzinfo=timezone.utc)
    grant = engine.protected_state.create_grant(
        principal, scope=("protected_cache", "queued_authority"), expires_at=issued + timedelta(hours=1), issued_at=issued
    )
    engine.protected_state.put_cache(
        grant.grant_id, key="incident:1", payload=b"protected projection",
        retention_expires_at=issued + timedelta(minutes=30), now=issued,
    )
    engine.protected_state.queue_authority(grant.grant_id, payload={"action": "acknowledge"}, now=issued)
    assert engine.protected_state.read_cache(grant.grant_id, key="incident:1", now=issued) == b"protected projection"
    receipt = engine.protected_state.revoke(
        grant.grant_id, action=GrantLifecycleAction.DEVICE_REVOCATION,
        actor="security-admin", reason="device lost", now=issued + timedelta(minutes=1),
    )
    assert receipt.purged_cache_entries == 1
    assert receipt.purged_queued_authority == 1
    assert engine.protected_state.metrics()["protected_cache_entries"] == 0
    assert engine.protected_state.metrics()["queued_authority_items"] == 0
    with pytest.raises(PermissionError, match="not active"):
        engine.protected_state.read_cache(grant.grant_id, key="incident:1", now=issued + timedelta(minutes=2))
    assert engine.protected_state.grants()[0].state.value == "revoked_policy"


def test_authenticated_logout_disables_token_and_purges_matching_grants(tmp_path) -> None:
    principal = PrincipalRef(principal_id="logout-operator", roles=(PrincipalRole.OPERATOR,), session_epoch=1, device_trust_epoch=2)
    auth = AuthManager([("logout-token-with-high-entropy-123", principal)])
    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    now = datetime.now(timezone.utc)
    grant = engine.protected_state.create_grant(
        principal, scope=("protected_cache", "queued_authority"), expires_at=now + timedelta(hours=1), issued_at=now
    )
    engine.protected_state.put_cache(
        grant.grant_id, key="private", payload=b"secret-ish",
        retention_expires_at=now + timedelta(minutes=10), now=now,
    )
    client = TestClient(create_app(engine, auth_manager=auth))
    headers = {"Authorization": "Bearer logout-token-with-high-entropy-123"}
    response = client.post("/v1/session/logout", headers=headers)
    assert response.status_code == 200
    assert response.json()["token_disabled"] is True
    assert response.json()["purge_receipts"][0]["purged_cache_entries"] == 1
    assert client.get("/v1/session", headers=headers).status_code == 401


def test_connector_drains_and_stops_without_hidden_receiver() -> None:
    observed: list[int] = []
    connector = BoundedBackgroundConnector("fixture-source", observed.append, queue_limit=8)
    connector.start()
    for value in range(5):
        connector.submit(value)
    receipt = connector.drain_and_stop(deadline_seconds=1.0)
    assert receipt.state is ConnectorState.STOPPED
    assert receipt.thread_alive is False
    assert receipt.accepted_items == 5
    assert receipt.processed_items == 5
    assert receipt.cancelled_items == 0
    assert observed == list(range(5))
    with pytest.raises(RuntimeError, match="not accepting"):
        connector.submit(99)
    time.sleep(0.03)
    assert observed == list(range(5))


def test_evidence_export_carries_highest_contiguous_authority_watermark(tmp_path) -> None:
    from sentinel_edge.domain.models import (
        EvidenceItem, EvidenceRetentionState, ExtractionConfidenceState, HazardKind,
        HealthState, MediaIntegrityState, ParserIsolationState, SourceStanding,
    )
    from sentinel_edge.exports import EvidenceExportSelection
    from sentinel_edge.storage import ArtifactClassification, ArtifactPolicy

    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    engine.run(load_scenario("fixtures/scenarios/simultaneous-event.json"))
    incident = next(item for item in engine.incidents.current() if item.hazard is HazardKind.WILDFIRE)
    ref = engine.artifacts.put_bytes(b"watermarked export", media_type="image/png", policy=ArtifactPolicy.incident_evidence())
    evidence = engine.evidence.ingest(EvidenceItem(
        incident_id=incident.incident_id,
        hazard=HazardKind.WILDFIRE,
        source_id="camera-watermark",
        source_standing=SourceStanding.FIRST_PARTY,
        media_integrity=MediaIntegrityState.ORIGINAL_VERIFIED,
        extraction_confidence_state=ExtractionConfidenceState.VERIFIED,
        extraction_confidence=1.0,
        freshness_state=HealthState.HEALTHY,
        claim_text="Watermark test frame",
        content_sha256=ref.sha256,
        origin_key="watermark-frame",
        retention_state=EvidenceRetentionState.RETAINED,
        parser_state=ParserIsolationState.SANDBOXED,
        rights_basis="device-owner",
        modality="image",
    ))
    expected = engine.incidents.authority_conformance()
    manifest = engine.exports.create(
        tmp_path / "evidence.zip",
        selections=(EvidenceExportSelection(
            evidence_id=evidence.evidence_id,
            classification=ArtifactClassification.RESTRICTED,
            include_content=False,
        ),),
    )
    assert manifest.authority_epoch_id == expected["epoch_id"]
    assert manifest.authority_watermark == expected["highest_contiguous_position"]
    verified = engine.exports.verify(tmp_path / "evidence.zip")
    assert verified["valid"] is True
    assert verified["manifest"]["authority_watermark"] == expected["highest_contiguous_position"]


def test_privacy_closure_blocks_live_protected_state_until_revocation(tmp_path) -> None:
    from sentinel_edge.privacy import build_privacy_closure

    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    principal = PrincipalRef(principal_id="candidate-user", roles=(PrincipalRole.VIEWER,))
    now = datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc)
    grant = engine.protected_state.create_grant(
        principal, scope=("protected_cache",), expires_at=now + timedelta(hours=1), issued_at=now
    )
    engine.protected_state.put_cache(
        grant.grant_id, key="candidate-cache", payload=b"must be purged",
        retention_expires_at=now + timedelta(minutes=5), now=now,
    )
    blocked = build_privacy_closure(engine, repository_root=tmp_path, generated_at=now)
    assert blocked["privacy_state_complete"] is False
    assert "active_protected_local_grants_present" in blocked["failures"]
    assert "protected_cache_entries_present" in blocked["failures"]
    engine.protected_state.revoke(
        grant.grant_id, action=GrantLifecycleAction.PLANNED_RETIREMENT,
        actor="candidate-builder", reason="candidate freeze", now=now + timedelta(minutes=1),
    )
    closed = build_privacy_closure(engine, repository_root=tmp_path, generated_at=now + timedelta(minutes=2))
    assert closed["privacy_state_complete"] is True
    assert closed["protected_local_state"]["active_grant_ids"] == []


def test_decommission_quiesces_connectors_purges_grants_and_retires_keys_without_erasure_claim(tmp_path) -> None:
    from sentinel_edge.operations import DecommissionManager, DecommissionState

    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    principal = PrincipalRef(principal_id="retiring-operator", roles=(PrincipalRole.OPERATOR,))
    now = datetime(2026, 8, 3, 10, 0, tzinfo=timezone.utc)
    grant = engine.protected_state.create_grant(
        principal, scope=("protected_cache",), expires_at=now + timedelta(hours=1), issued_at=now
    )
    engine.protected_state.put_cache(
        grant.grant_id, key="retire-me", payload=b"protected",
        retention_expires_at=now + timedelta(minutes=30), now=now,
    )
    _, _, audit_public = raw_keys()
    _, _, source_public = raw_keys()
    engine.key_lifecycle.register(
        identity_id="node-audit", generation=1, purpose=KeyPurpose.AUDIT_SIGNING,
        public_key_raw=audit_public, policy_version="audit-v1", actor="admin", reason="activate",
        active_from=now, registered_at=now,
    )
    engine.key_lifecycle.register(
        identity_id="node-source", generation=1, purpose=KeyPurpose.SOURCE_SIGNING,
        public_key_raw=source_public, policy_version="source-v1", actor="admin", reason="activate",
        active_from=now, registered_at=now,
    )
    observed: list[int] = []
    connector = BoundedBackgroundConnector("decommission-source", observed.append)
    connector.start()
    connector.submit(1)
    receipt = DecommissionManager(engine).execute(
        actor="field-admin", reason="node retirement", connectors=(connector,),
        connector_deadline_seconds=1.0, network_exposure_removed=True, now=now + timedelta(minutes=1),
    )
    assert receipt.state is DecommissionState.COMPLETED
    assert receipt.blockers == ()
    assert receipt.connector_receipts[0]["thread_alive"] is False
    assert receipt.protected_state_purge_receipts[0]["purged_cache_entries"] == 1
    states = {item.purpose.value: item.state.value for item in engine.key_lifecycle.records()}
    assert states["audit_signing"] == "retired"
    assert states["source_signing"] == "revoked_policy"
    assert receipt.historical_identity_preserved is True
    assert receipt.secure_erasure_claimed is False


def test_decommission_reports_unresolved_effects_instead_of_claiming_completion(tmp_path) -> None:
    from sentinel_edge.operations import DecommissionManager, DecommissionState
    from sentinel_edge.domain.models import EvidenceItem, EvidenceRetentionState, ExtractionConfidenceState, HazardKind, HealthState, MediaIntegrityState, ParserIsolationState, SourceStanding
    from sentinel_edge.privacy import DispositionAction

    engine = DeterministicScenarioEngine(state_dir=tmp_path / "state")
    engine.run(load_scenario("fixtures/scenarios/simultaneous-event.json"))
    incident = next(item for item in engine.incidents.current() if item.hazard is HazardKind.WILDFIRE)
    ref = engine.artifacts.put_bytes(b"decommission-evidence", media_type="image/png", policy=__import__('sentinel_edge.storage', fromlist=['ArtifactPolicy']).ArtifactPolicy.incident_evidence())
    evidence = engine.evidence.ingest(EvidenceItem(
        incident_id=incident.incident_id, hazard=HazardKind.WILDFIRE, source_id="camera",
        source_standing=SourceStanding.FIRST_PARTY, media_integrity=MediaIntegrityState.ORIGINAL_VERIFIED,
        extraction_confidence_state=ExtractionConfidenceState.VERIFIED, extraction_confidence=1.0,
        freshness_state=HealthState.HEALTHY, claim_text="retained frame", content_sha256=ref.sha256,
        origin_key="decommission-frame", retention_state=EvidenceRetentionState.RETAINED,
        parser_state=ParserIsolationState.SANDBOXED, rights_basis="device-owner", modality="image",
    ))
    now = datetime(2026, 8, 3, 11, 0, tzinfo=timezone.utc)
    request = engine.disposition.create_request(
        action=DispositionAction.ERASE, evidence_ids=(evidence.evidence_id,), subject_ref="subject-1",
        subject_basis="consent", actor="privacy-admin", reason="pending erasure",
        deadline=now + timedelta(days=1), created_at=now,
    )
    receipt = DecommissionManager(engine).execute(
        actor="field-admin", reason="attempted retirement", network_exposure_removed=False,
        now=now + timedelta(minutes=1),
    )
    assert receipt.state is DecommissionState.BLOCKED
    assert str(request.request_id) in receipt.unresolved_disposition_request_ids
    assert "unresolved_disposition_requests" in receipt.blockers
    assert "pending_notification_effects" in receipt.blockers
    assert "network_exposure_not_removed" in receipt.blockers
