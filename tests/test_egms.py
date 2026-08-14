import pytest

from sentinel_edge.integrations.egms import EgmsHistoricalContext


def test_egms_context_preserves_release_product_and_tier() -> None:
    context = EgmsHistoricalContext("2020-2024", "L3", "fixture:egms-2020-2024")
    assert context.as_metadata() == {"release_period": "2020-2024", "product": "L3", "api_or_fixture_ref": "fixture:egms-2020-2024", "tier": "T3", "historical_only": True}


def test_egms_context_rejects_unbounded_or_non_t3_metadata() -> None:
    with pytest.raises(ValueError, match="bounded"):
        EgmsHistoricalContext("latest", "L3", "fixture:egms")
    with pytest.raises(ValueError, match="historical T3"):
        EgmsHistoricalContext("2020-2024", "L3", "fixture:egms", tier="T2")
