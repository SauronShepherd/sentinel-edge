from pathlib import PurePosixPath
from uuid import uuid4

import pytest
from pydantic import ValidationError

from sentinel_edge.exports import ExportMember
from sentinel_edge.storage import ArtifactRef
from sentinel_edge.storage.artifact_governance import ArtifactClassification
from sentinel_edge.storage.artifact_governance import ArtifactReferenceKind, ArtifactPolicy
from sentinel_edge.storage import ContentAddressedArtifactStore


def test_artifact_reference_is_opaque_and_export_member_path_is_archive_relative() -> None:
    ref = ArtifactRef("a" * 64, "aa/" + "a" * 62, 3, "application/octet-stream")
    assert ref.sha256 == "a" * 64
    assert PurePosixPath(ref.relative_path).is_absolute() is False

    member = ExportMember(
        path="evidence/item/metadata.json",
        bytes=3,
        sha256="a" * 64,
        media_type="application/json",
        classification=ArtifactClassification.INTERNAL,
        source_evidence_id=uuid4(),
        target_binding="artifact-sha256:" + "a" * 64,
        transformation="none",
        rights_decision="internal:active",
        lifecycle_state="available",
    )
    assert PurePosixPath(member.path).is_absolute() is False
    assert member.target_binding.startswith("artifact-sha256:")


@pytest.mark.parametrize("path", ["/etc/passwd", "C:/private/artifact.bin", "../outside.bin"])
def test_export_member_rejects_absolute_or_cross_owned_paths(path: str) -> None:
    with pytest.raises(ValidationError):
        ExportMember(
            path=path,
            bytes=1,
            sha256="a" * 64,
            media_type="application/octet-stream",
            classification=ArtifactClassification.INTERNAL,
            source_evidence_id=uuid4(),
            target_binding="artifact-sha256:" + "a" * 64,
            transformation="none",
            rights_decision="internal:active",
            lifecycle_state="available",
        )


def test_active_incident_reference_blocks_artifact_deletion(tmp_path) -> None:
    store = ContentAddressedArtifactStore(tmp_path / "artifacts")
    ref = store.put_bytes(b"incident-evidence", media_type="application/octet-stream", policy=ArtifactPolicy.incident_evidence())
    store.add_reference(ref.sha256, kind=ArtifactReferenceKind.INCIDENT_HOLD, owner="incident:1", reason="active incident evidence")
    with pytest.raises(PermissionError, match="active references"):
        store.delete_digest(ref.sha256)
    assert store.verify(ref)
    store.close()
