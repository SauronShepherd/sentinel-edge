"""C2PA-style export credentials: provenance of transformations, never sensor truth."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class C2paExportCredential:
    asset_digest: str
    transformations: tuple[str, ...]
    issuer: str
    sensor_truth_claim: bool = False

    def __post_init__(self) -> None:
        if not self.asset_digest.strip() or not self.issuer.strip():
            raise ValueError("asset_digest and issuer are required")
        if not self.transformations or any(not item.strip() for item in self.transformations):
            raise ValueError("at least one transformation is required")
        if self.sensor_truth_claim:
            raise ValueError("C2PA credential cannot claim sensor truth")

    def as_export_metadata(self) -> dict[str, object]:
        return {
            "credential_type": "c2pa",
            "asset_digest": self.asset_digest,
            "issuer": self.issuer,
            "transformations": list(self.transformations),
            "sensor_truth_claim": False,
        }
