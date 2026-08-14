"""Hash- and lineage-bound dataset variant identities."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DatasetVariantKind(StrEnum):
    RAW = "raw"
    HARMONIZED = "harmonized"
    CORRECTED = "corrected"
    RELABELLED = "relabelled"


@dataclass(frozen=True)
class DatasetVariant:
    dataset_id: str
    variant_id: str
    kind: DatasetVariantKind
    content_sha256: str
    preprocessing_sha256: str
    split_manifest_sha256: str
    parent_variant_id: str | None = None

    def __post_init__(self) -> None:
        if any(not value.strip() for value in (self.dataset_id, self.variant_id, self.content_sha256, self.preprocessing_sha256, self.split_manifest_sha256)):
            raise ValueError("dataset variant identity and lineage digests are required")
        if self.kind is DatasetVariantKind.RAW and self.parent_variant_id is not None:
            raise ValueError("raw dataset variant cannot have a parent")
        if self.kind is not DatasetVariantKind.RAW and not self.parent_variant_id:
            raise ValueError("derived dataset variant requires a parent")


def assert_variants_distinct(left: DatasetVariant, right: DatasetVariant) -> None:
    if left.variant_id == right.variant_id and (left.kind is not right.kind or left.content_sha256 != right.content_sha256 or left.preprocessing_sha256 != right.preprocessing_sha256 or left.split_manifest_sha256 != right.split_manifest_sha256):
        raise ValueError("dataset variant identity conflict")
    if left.variant_id != right.variant_id and left.content_sha256 == right.content_sha256 and left.preprocessing_sha256 == right.preprocessing_sha256 and left.split_manifest_sha256 == right.split_manifest_sha256 and left.kind is not right.kind:
        raise ValueError("dataset variants cannot silently share identity across kinds")
