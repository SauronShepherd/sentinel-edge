"""Machine-readable model/data/source card index with deterministic resolution."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Card(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    card_id: str
    card_type: str
    profile_id: str
    source_id: str
    title: str = Field(min_length=1)


class CardIndex(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema: str = "sentinel-edge-card-index/1.0"
    cards: tuple[Card, ...]

    def resolve(self, *, profile_id: str, source_id: str) -> tuple[Card, ...]:
        return tuple(item for item in self.cards if item.profile_id == profile_id and item.source_id == source_id)
