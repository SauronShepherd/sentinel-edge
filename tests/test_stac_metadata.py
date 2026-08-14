from datetime import datetime, timezone

import pytest

from sentinel_edge.integrations import StacAsset, build_stac_item


def test_stac_item_preserves_asset_provenance_and_license() -> None:
    item = build_stac_item(
        item_id="sentinel-context-1",
        captured_at=datetime(2026, 8, 12, 16, 0, tzinfo=timezone.utc),
        assets={"thumbnail": StacAsset(href="fixture://context/1.png", media_type="image/png", roles=("thumbnail",))},
        license="CC-BY-4.0",
        provenance="fixture:context-catalog-v1",
        properties={"platform": "fixture-satellite"},
    )
    assert item.stac_version == "1.0.0"
    assert item.license == "CC-BY-4.0"
    assert item.provenance == "fixture:context-catalog-v1"
    assert item.assets["thumbnail"].href.startswith("fixture://")


def test_stac_item_rejects_unresolved_license_and_unbounded_assets() -> None:
    with pytest.raises(ValueError, match="resolved license"):
        build_stac_item(item_id="bad", captured_at=datetime.now(timezone.utc), assets={"a": StacAsset(href="x", media_type="text/plain")}, license="NOASSERTION", provenance="fixture")
    assets = {str(index): StacAsset(href=f"fixture://{index}", media_type="application/octet-stream") for index in range(65)}
    with pytest.raises(ValueError, match="1..64"):
        build_stac_item(item_id="too-many", captured_at=datetime.now(timezone.utc), assets=assets, license="MIT", provenance="fixture")
