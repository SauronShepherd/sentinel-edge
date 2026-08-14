from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from sentinel_edge.storage import (
    ArtifactBudgetPolicy,
    ArtifactClassification,
    ArtifactDeletionPolicy,
    ArtifactEncryption,
    ArtifactExportPolicy,
    ArtifactPolicy,
    ArtifactReferenceKind,
    ArtifactRetention,
    ArtifactScope,
    ContentAddressedArtifactStore,
)


def policy(*, expires: datetime | None = None) -> ArtifactPolicy:
    return ArtifactPolicy(
        classification=ArtifactClassification.INTERNAL,
        retention=ArtifactRetention.EPHEMERAL,
        encryption=ArtifactEncryption.NODE_AT_REST,
        export_policy=ArtifactExportPolicy.ALLOWED,
        deletion_policy=ArtifactDeletionPolicy.GC_ALLOWED,
        retention_expires_at=expires,
    )


def test_secret_prohibited_persistence_and_scope_budgets_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="secret-prohibited"):
        ArtifactPolicy(
            classification=ArtifactClassification.SECRET_PROHIBITED,
            retention=ArtifactRetention.OPERATIONAL,
            encryption=ArtifactEncryption.NODE_AT_REST,
            export_policy=ArtifactExportPolicy.PROHIBITED,
            deletion_policy=ArtifactDeletionPolicy.MANUAL_ONLY,
        )
    store = ContentAddressedArtifactStore(
        tmp_path / "artifacts",
        max_bytes=1024,
        reserve_bytes=64,
        budget_policy=ArtifactBudgetPolicy(
            node_max_objects=10,
            per_source_max_objects=2,
            per_source_max_bytes=8,
            per_incident_max_objects=10,
            per_incident_max_bytes=1024,
            per_run_max_objects=10,
            per_run_max_bytes=1024,
            per_candidate_max_objects=10,
            per_candidate_max_bytes=1024,
        ),
    )
    scope = ArtifactScope(source_id="source-a")
    store.put_bytes(b"aaaa", policy=policy(), scope=scope)
    store.put_bytes(b"bbbb", policy=policy(), scope=scope)
    with pytest.raises(OSError, match="object-count budget"):
        store.put_bytes(b"cccc", policy=policy(), scope=scope)
    usage = store.catalog.usage()
    assert usage["registrations"] == 2
    assert usage["by_classification"]["internal"]["logical_bytes"] == 8


def test_gc_respects_active_references_and_retention(tmp_path: Path) -> None:
    now = datetime(2026, 8, 3, tzinfo=timezone.utc)
    store = ContentAddressedArtifactStore(tmp_path / "artifacts", max_bytes=1024, reserve_bytes=64)
    ref = store.put_bytes(b"temporary", policy=policy(expires=now - timedelta(seconds=1)))
    hold = store.add_reference(
        ref.sha256,
        kind=ArtifactReferenceKind.RELEASE_CANDIDATE,
        owner="candidate-1",
        reason="bound release proof",
    )
    blocked = store.collect_garbage(now=now)
    assert blocked["deleted"] == []
    assert ref.sha256 in blocked["blocked"]
    store.catalog.remove_reference(hold.reference_id)
    result = store.collect_garbage(now=now)
    assert result["deleted"] == [ref.sha256]
    assert not (store.root / ref.relative_path).exists()


def test_finalized_reference_rejects_change_after_reference(tmp_path: Path) -> None:
    store = ContentAddressedArtifactStore(tmp_path / "artifacts", max_bytes=1024, reserve_bytes=64)
    ref = store.put_bytes(b"finalized", policy=policy())
    store.add_reference(
        ref.sha256,
        kind=ArtifactReferenceKind.RELEASE_CANDIDATE,
        owner="candidate-1",
        reason="immutable finalized evidence",
    )
    path = store.root / ref.relative_path
    path.write_bytes(b"changed-after-reference")
    with pytest.raises(RuntimeError, match="digest mismatch after reference"):
        store.read_bytes(ref.sha256)


def test_all_scope_budget_dimensions_and_node_count_are_enforced(tmp_path: Path) -> None:
    budgets = ArtifactBudgetPolicy(
        node_max_objects=4,
        per_source_max_objects=1,
        per_source_max_bytes=16,
        per_incident_max_objects=1,
        per_incident_max_bytes=16,
        per_run_max_objects=1,
        per_run_max_bytes=16,
        per_candidate_max_objects=1,
        per_candidate_max_bytes=16,
    )
    store = ContentAddressedArtifactStore(tmp_path / "artifacts", max_bytes=4096, reserve_bytes=64, budget_policy=budgets)
    store.put_bytes(b"source", policy=policy(), scope=ArtifactScope(source_id="s1"))
    store.put_bytes(b"incident", policy=policy(), scope=ArtifactScope(incident_id="i1"))
    store.put_bytes(b"run", policy=policy(), scope=ArtifactScope(scenario_run_id="r1"))
    store.put_bytes(b"candidate", policy=policy(), scope=ArtifactScope(release_candidate_id="c1"))
    with pytest.raises(OSError, match="node object-count"):
        store.put_bytes(b"extra", policy=policy(), scope=ArtifactScope(source_id="s2"))


def test_artifact_policy_is_required_for_every_content_addressed_write(tmp_path: Path) -> None:
    store = ContentAddressedArtifactStore(tmp_path / "artifacts")
    with pytest.raises(TypeError, match="policy"):
        store.put_bytes(b"unclassified")  # type: ignore[call-arg]
