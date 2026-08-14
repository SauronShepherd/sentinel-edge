from sentinel_edge.release.claim_lineage import ClaimDisposition, ClaimInfluenceManifest, resolve_claim_lineage


def manifest() -> ClaimInfluenceManifest:
    return ClaimInfluenceManifest("dataset-v2", "a" * 64, "b" * 64, "c" * 64)


def test_claim_requires_exact_available_influence_variant() -> None:
    current = resolve_claim_lineage("claim-1", manifest(), available_variant_ids={"dataset-v2"})
    assert current.disposition is ClaimDisposition.CURRENT
    missing = resolve_claim_lineage("claim-1", manifest(), available_variant_ids=set())
    assert missing.disposition is ClaimDisposition.REVIEW_REQUIRED


def test_corrected_claim_is_explicitly_superseded() -> None:
    result = resolve_claim_lineage("claim-old", manifest(), available_variant_ids={"dataset-v2"}, replacement_claim_id="claim-new")
    assert result.disposition is ClaimDisposition.SUPERSEDED
    assert result.replacement_claim_id == "claim-new"
