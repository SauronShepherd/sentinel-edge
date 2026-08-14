"""Bounded EGMS historical machine-to-machine context (2020-2024)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EgmsHistoricalContext:
    release_period: str
    product: str
    api_or_fixture_ref: str
    tier: str = "T3"
    historical_only: bool = True

    def __post_init__(self) -> None:
        if self.release_period not in {"2020-2024", "2020–2024"}:
            raise ValueError("EGMS context must use the bounded 2020-2024 release period")
        if not all(value.strip() for value in (self.product, self.api_or_fixture_ref)):
            raise ValueError("EGMS product and API/fixture reference are required")
        if self.tier != "T3" or not self.historical_only:
            raise ValueError("EGMS context must remain historical T3 context")

    def as_metadata(self) -> dict[str, str | bool]:
        return {"release_period": self.release_period, "product": self.product, "api_or_fixture_ref": self.api_or_fixture_ref, "tier": self.tier, "historical_only": True}
