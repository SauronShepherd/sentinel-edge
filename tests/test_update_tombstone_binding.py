from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from sentinel_edge.storage import ArtifactPolicy
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from sentinel_edge.domain.models import EvidenceContentState, EvidenceItem, EvidenceRetentionState, ExtractionConfidenceState, HazardKind, HealthState, MediaIntegrityState, ParserIsolationState, RuntimeMode, SourceStanding
from sentinel_edge.privacy import build_tombstone_journal
from sentinel_edge.scenario import DeterministicScenarioEngine, load_scenario
from sentinel_edge.update import OfflineUpdateManager, build_update_bundle


def state_with_tombstone(tmp_path: Path) -> Any:
    state = tmp_path / "state"
    engine = DeterministicScenarioEngine(state_dir=state)
    engine.run(load_scenario("fixtures/scenarios/simultaneous-event.json"))
    incident = next(item for item in engine.incidents.current() if item.hazard is HazardKind.WILDFIRE)
    ref = engine.artifacts.put_bytes(b"delete-before-update", policy=ArtifactPolicy.incident_evidence())
    item = engine.evidence.ingest(EvidenceItem(
        incident_id=incident.incident_id,
        hazard=HazardKind.WILDFIRE,
        source_id="camera-1",
        source_standing=SourceStanding.FIRST_PARTY,
        media_integrity=MediaIntegrityState.ORIGINAL_VERIFIED,
        extraction_confidence_state=ExtractionConfidenceState.VERIFIED,
        extraction_confidence=1.0,
        freshness_state=HealthState.HEALTHY,
        claim_text="delete me",
        content_sha256=ref.sha256,
        origin_key="frame-delete",
        retention_state=EvidenceRetentionState.RETAINED,
        parser_state=ParserIsolationState.SANDBOXED,
        rights_basis="device-owner",
    ))
    engine.evidence.transition(item.evidence_id, to_state=EvidenceContentState.DELETED, expected_version=1, actor="privacy-admin", reason="erase")
    return state, build_tombstone_journal(engine.evidence.store)


def test_update_is_bound_to_minimum_tombstone_watermark(tmp_path: Path) -> None:
    state, journal = state_with_tombstone(tmp_path)
    source = tmp_path / "source"
    target = source / "src" / "sentinel_edge" / "__init__.py"
    target.parent.mkdir(parents=True)
    target.write_text('__version__ = "0.12.1"\n', encoding="utf-8")
    private = Ed25519PrivateKey.generate()
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
    bundle = build_update_bundle(
        tmp_path / "update.zip",
        source_root=source,
        target_paths=["src/sentinel_edge/__init__.py"],
        private_key=private,
        bundle_id="privacy-bound-update",
        version=1,
        created_at=now,
        expires_at=now + timedelta(days=1),
        compatible_min_version="0.12.0",
        compatible_max_version="0.12.9",
        minimum_tombstone_authority_position=journal.source_authority_position,
        required_tombstone_journal_sha256=journal.payload_sha256,
    )
    manager = OfflineUpdateManager(state, private.public_key(), current_project_version="0.12.0", mode=RuntimeMode.FIELD_LAB)
    _, result = manager.verify(bundle, now=now + timedelta(minutes=1))
    assert "tombstone_requirement_satisfied" in result.reason_codes

    stale = OfflineUpdateManager(tmp_path / "stale-state", private.public_key(), current_project_version="0.12.0", mode=RuntimeMode.FIELD_LAB)
    with pytest.raises(ValueError, match="newer privacy tombstone watermark"):
        stale.verify(bundle, now=now + timedelta(minutes=1))


def test_update_cannot_target_protected_evidence_or_privacy_paths(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = source / "artifacts" / "forbidden.bin"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"forbidden")
    private = Ed25519PrivateKey.generate()
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="protected"):
        build_update_bundle(
            tmp_path / "bad.zip",
            source_root=source,
            target_paths=["artifacts/forbidden.bin"],
            private_key=private,
            bundle_id="bad",
            version=1,
            created_at=now,
            expires_at=now + timedelta(days=1),
            compatible_min_version="0.12.0",
            compatible_max_version="0.12.9",
        )
