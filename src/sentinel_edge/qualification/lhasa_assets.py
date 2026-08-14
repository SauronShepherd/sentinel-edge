"""Offline NASA LHASA/IMERG context-asset cards with non-authoritative role bounds."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LhasaContextAssetCard:
    product: str
    version: str
    role: str
    latency_coverage: str
    archive_catalog_mismatch: str | None = None
    local_truth_authority: bool = False

    def __post_init__(self) -> None:
        if (self.product, self.version) not in {("NASA LHASA", "L4 v2.0.0"), ("IMERG/LHASA Exposure Maps", "1.0")}:
            raise ValueError("unsupported LHASA/IMERG product version")
        if self.role not in {"offline-context", "potential-exposure-context"} or not self.latency_coverage.strip():
            raise ValueError("asset role and latency/coverage description are required")
        if self.local_truth_authority:
            raise ValueError("context assets cannot be local-truth authority")

    def as_card(self) -> dict[str, object]:
        return {"product": self.product, "version": self.version, "role": self.role, "latency_coverage": self.latency_coverage, "archive_catalog_mismatch": self.archive_catalog_mismatch, "local_truth_authority": False}
