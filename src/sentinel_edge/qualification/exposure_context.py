"""Offline exposure-context asset policy."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExposureContextAsset:
    asset_id: str
    source_kind: str
    attribution: str
    preclipped: bool = True
    offline: bool = True

    def __post_init__(self) -> None:
        if not self.asset_id.strip() or not self.source_kind.strip() or not self.attribution.strip():
            raise ValueError("exposure context requires asset identity and attribution")
        if not self.preclipped or not self.offline:
            raise ValueError("exposure context must be preclipped and offline")
        if self.source_kind.lower() not in {"ghsl", "worldpop", "osm"}:
            raise ValueError("unsupported exposure context source")

    def decision_scope(self) -> str:
        return "potential_exposure_context_only"
