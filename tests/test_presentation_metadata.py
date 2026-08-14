from sentinel_edge.gateway.presentation_metadata import PresentationMetadata, apply_presentation_metadata


def test_presentation_metadata_cannot_mutate_authoritative_state() -> None:
    state = {"state": "confirmed", "version": 4}
    result = apply_presentation_metadata(state, PresentationMetadata("Friendly label", "display-v1"))
    assert result["authoritative_state"] == state
    assert result["presentation"]["authoritative"] is False
    assert "state" not in result["presentation"]
