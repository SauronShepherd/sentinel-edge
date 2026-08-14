"""Offline research/evaluation card for 2026 JRC European flood-depth maps."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JrcFloodDepthMapCard:
    coverage: str = "2015-2024"
    resolution_m: int = 20
    derivation: str = "GFM/Sentinel-1"
    encoding: str = "centimetres"
    permanent_water_sentinel: str = "permanent-water"
    license_id: str = "CC BY 4.0"
    local_truth_authority: bool = False

    def __post_init__(self) -> None:
        if self.coverage != "2015-2024" or self.resolution_m != 20 or self.derivation != "GFM/Sentinel-1" or self.encoding != "centimetres" or self.permanent_water_sentinel != "permanent-water" or self.license_id != "CC BY 4.0":
            raise ValueError("JRC flood-depth map card metadata mismatch")
        if self.local_truth_authority:
            raise ValueError("research map cannot be current local truth")
