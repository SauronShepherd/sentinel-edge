import pytest

from sentinel_edge.release.cards import Card, CardIndex


def test_card_index_resolves_model_data_source_card_by_profile_and_source() -> None:
    index = CardIndex(cards=(Card(card_id="wildfire-card", card_type="model", profile_id="wildfire-deterministic-v2", source_id="camera-1", title="Wildfire model"),))
    resolved = index.resolve(profile_id="wildfire-deterministic-v2", source_id="camera-1")
    assert [item.card_id for item in resolved] == ["wildfire-card"]
    assert index.resolve(profile_id="other", source_id="camera-1") == ()


def test_card_requires_nonempty_title() -> None:
    with pytest.raises(ValueError):
        Card(card_id="x", card_type="source", profile_id="p", source_id="s", title="")
