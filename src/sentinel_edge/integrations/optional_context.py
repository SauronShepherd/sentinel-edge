"""Optional standards context records with explicit non-authority semantics."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WIS2ContextItem:
    item_id: str
    origin_centre: str
    topic: str
    metadata_id: str
    licence_id: str
    optional: bool = True

    def __post_init__(self) -> None:
        if any(not value.strip() for value in (self.item_id, self.origin_centre, self.topic, self.metadata_id, self.licence_id)):
            raise ValueError("WIS2 identity, origin, topic, metadata, and licence are required")

    @property
    def h0_dependency(self) -> bool:
        return False

    def normalized_context(self) -> dict[str, str | bool]:
        return {"item_id": self.item_id, "origin_centre": self.origin_centre, "topic": self.topic,
                "metadata_id": self.metadata_id, "licence_id": self.licence_id, "optional": self.optional}

    def trace_normalized_context(self, normalized: dict[str, object]) -> bool:
        return all(normalized.get(key) == value for key, value in self.normalized_context().items())


@dataclass(frozen=True)
class EidaNetworkRecord:
    network: str
    station: str
    rights_status: str
    availability_status: str
    evaluation_only: bool = True

    def __post_init__(self) -> None:
        if any(not value.strip() for value in (self.network, self.station, self.rights_status, self.availability_status)):
            raise ValueError("EIDA network rights and availability fields are required")

    @property
    def local_trigger_dependency(self) -> bool:
        return False
