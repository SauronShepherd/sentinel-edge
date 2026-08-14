"""Exact manifest binding and claim supersession decisions."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ClaimDisposition(StrEnum):
    CURRENT = "current"
    SUPERSEDED = "superseded"
    REVIEW_REQUIRED = "review_required"


@dataclass(frozen=True)
class ClaimInfluenceManifest:
    dataset_variant_id: str
    dataset_sha256: str
    preprocessing_sha256: str
    split_manifest_sha256: str


@dataclass(frozen=True)
class ClaimLineageDecision:
    claim_id: str
    disposition: ClaimDisposition
    manifest: ClaimInfluenceManifest
    replacement_claim_id: str | None
    reason_code: str


def resolve_claim_lineage(claim_id: str, manifest: ClaimInfluenceManifest, *, available_variant_ids: set[str], replacement_claim_id: str | None = None) -> ClaimLineageDecision:
    if not claim_id.strip() or not manifest.dataset_variant_id.strip():
        raise ValueError("claim and dataset variant identities are required")
    if manifest.dataset_variant_id not in available_variant_ids:
        return ClaimLineageDecision(claim_id, ClaimDisposition.REVIEW_REQUIRED, manifest, replacement_claim_id, "influencing_variant_unavailable")
    if replacement_claim_id:
        return ClaimLineageDecision(claim_id, ClaimDisposition.SUPERSEDED, manifest, replacement_claim_id, "superseded_by_replacement_claim")
    return ClaimLineageDecision(claim_id, ClaimDisposition.CURRENT, manifest, None, "exact_influence_manifest_resolved")
