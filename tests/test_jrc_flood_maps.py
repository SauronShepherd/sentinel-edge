from sentinel_edge.qualification.jrc_flood_maps import JrcFloodDepthMapCard


def test_jrc_map_card_preserves_exact_research_metadata_and_role() -> None:
    card = JrcFloodDepthMapCard()
    assert card.coverage == "2015-2024"
    assert card.resolution_m == 20
    assert card.license_id == "CC BY 4.0"
    assert card.local_truth_authority is False
