import pytest

from sentinel_edge.qualification.dataset_variants import DatasetVariant, DatasetVariantKind, assert_variants_distinct


def variant(kind: DatasetVariantKind, variant_id: str, parent: str | None = None) -> DatasetVariant:
    return DatasetVariant("flood-data", variant_id, kind, variant_id + "a" * 62, kind.value + "b" * 58, variant_id + "c" * 62, parent)


def test_dataset_variants_require_explicit_parent_and_distinct_identity() -> None:
    raw = variant(DatasetVariantKind.RAW, "raw-v1")
    harmonized = variant(DatasetVariantKind.HARMONIZED, "harm-v1", "raw-v1")
    assert raw.variant_id != harmonized.variant_id
    with pytest.raises(ValueError, match="parent"):
        variant(DatasetVariantKind.CORRECTED, "corrected-v1")


def test_same_digests_cannot_be_silently_relabelled_as_another_kind() -> None:
    raw = variant(DatasetVariantKind.RAW, "raw-v1")
    relabelled = DatasetVariant("flood-data", "label-v1", DatasetVariantKind.RELABELLED, raw.content_sha256, raw.preprocessing_sha256, raw.split_manifest_sha256, "raw-v1")
    with pytest.raises(ValueError, match="silently"):
        assert_variants_distinct(raw, relabelled)
