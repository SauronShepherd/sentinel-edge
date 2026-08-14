import pytest

from sentinel_edge.qualification.lineage import DerivedArtifactKind, GovernedLineageLink


def test_lineage_links_claim_and_retained_bytes_to_source_item() -> None:
    claim = GovernedLineageLink(artifact_id="claim-1", artifact_kind=DerivedArtifactKind.CLAIM,
        governed_source_item_id="e-1", source_content_sha256="a" * 64, transformation_id="ocr-v1")
    retained = GovernedLineageLink(artifact_id="bytes-1", artifact_kind=DerivedArtifactKind.RETAINED_BYTES,
        governed_source_item_id="e-1", source_content_sha256="a" * 64, transformation_id="retain-v1")
    assert claim.governed_source_item_id == retained.governed_source_item_id


def test_lineage_requires_content_digest() -> None:
    with pytest.raises(ValueError):
        GovernedLineageLink(artifact_id="x", artifact_kind=DerivedArtifactKind.CLAIM,
            governed_source_item_id="e", source_content_sha256="bad", transformation_id="t")
