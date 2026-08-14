import pytest

from sentinel_edge.gateway.kiosk import KioskAsset, asset_digest, assess_kiosk_readiness


def test_kiosk_is_offline_ready_only_after_local_load() -> None:
    asset = KioskAsset(path="/index.html", sha256=asset_digest(b"local"))
    not_ready = assess_kiosk_readiness((asset,), local_cache_paths=frozenset())
    assert not_ready.offline_ready is False
    ready = assess_kiosk_readiness((asset,), local_cache_paths=frozenset({"/index.html"}))
    assert ready.offline_ready is True
    assert ready.low_distraction is True and ready.reduced_motion is True


def test_kiosk_requires_versioned_assets() -> None:
    with pytest.raises(ValueError):
        assess_kiosk_readiness((), local_cache_paths=frozenset())
