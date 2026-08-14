"""Deterministic readiness contract for the low-distraction offline kiosk UI."""

from __future__ import annotations

from hashlib import sha256

from pydantic import BaseModel, ConfigDict, Field


class KioskAsset(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class KioskReadiness(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    assets: tuple[KioskAsset, ...]
    local_load_complete: bool
    offline_ready: bool
    low_distraction: bool = True
    reduced_motion: bool = True


def assess_kiosk_readiness(
    assets: tuple[KioskAsset, ...], *, local_cache_paths: frozenset[str],
    low_distraction: bool = True, reduced_motion: bool = True,
) -> KioskReadiness:
    if not assets:
        raise ValueError("kiosk requires at least one versioned local asset")
    complete = all(asset.path in local_cache_paths for asset in assets)
    return KioskReadiness(assets=assets, local_load_complete=complete, offline_ready=complete,
                          low_distraction=low_distraction, reduced_motion=reduced_motion)


def asset_digest(content: bytes) -> str:
    return sha256(content).hexdigest()
