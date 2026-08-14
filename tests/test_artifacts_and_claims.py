from pathlib import Path

import pytest

from sentinel_edge.domain.models import ClaimClass, ClaimRecord
from sentinel_edge.release import ClaimRegistry
from sentinel_edge.storage import ArtifactPolicy, ContentAddressedArtifactStore
from sentinel_edge.exports import EvidenceExportManifest


def test_content_addressed_artifacts_are_atomic_deduplicated_and_verified(tmp_path: Path) -> None:
    store = ContentAddressedArtifactStore(tmp_path / "artifacts", max_bytes=2048, reserve_bytes=256)
    first = store.put_bytes(b"evidence", media_type="text/plain", policy=ArtifactPolicy.internal_operational())
    second = store.put_bytes(b"evidence", media_type="text/plain", policy=ArtifactPolicy.internal_operational())
    assert first == second
    assert store.verify(first)
    temp = store.root / ".tmp-interrupted"
    temp.write_bytes(b"partial")
    assert store.quarantine_incomplete() == (".quarantine/.tmp-interrupted",)


def test_export_manifest_carries_persistent_research_warning() -> None:
    fields = EvidenceExportManifest.model_fields
    assert "research_warning" in fields
    assert "not an official warning service" in fields["research_warning"].default


def test_capacity_reserve_blocks_noncritical_artifact_growth(tmp_path: Path) -> None:
    store = ContentAddressedArtifactStore(tmp_path / "artifacts", max_bytes=32, reserve_bytes=8)
    with pytest.raises(OSError, match="reserve"):
        store.put_bytes(b"x" * 25, policy=ArtifactPolicy.internal_operational())


def test_claim_registry_requires_evidence_closure_for_measured_claims(tmp_path: Path) -> None:
    registry = ClaimRegistry()
    with pytest.raises(ValueError, match="measured"):
        registry.add(ClaimRecord(claim_id="c1", claim_class=ClaimClass.MEASURED, statement="latency", artifact_refs=()))
    registry.add(ClaimRecord(claim_id="c2", claim_class=ClaimClass.SIMULATED, statement="fixture result", artifact_refs=("sha256:abc",)))
    store = ContentAddressedArtifactStore(tmp_path / "claims")
    ref = registry.write(store)
    assert store.verify(ref)


def test_measured_claim_verification_resolves_all_exact_hashes() -> None:
    claim = ClaimRecord(claim_id="measured", claim_class=ClaimClass.MEASURED, statement="measured", artifact_refs=("sha256:" + "a" * 64,), capability_hashes=("b" * 64,), config_hashes=("c" * 64,), model_hashes=("d" * 64,))
    assert ClaimRegistry.verify_measured_claim(claim, artifact_digests={"a" * 64}, capability_hashes={"b" * 64}, config_hashes={"c" * 64}, model_hashes={"d" * 64}) == ()
