from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4
import re
from types import MappingProxyType
from collections.abc import Mapping

_NAME = re.compile(r"^[a-z][a-z0-9_.-]{1,62}$")

@dataclass(frozen=True, slots=True)
class Envelope:
    type: str
    source: str
    data: Mapping[str, object]
    producer: str | None = None
    subject: str | None = None
    id: UUID = field(default_factory=uuid4)
    time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    specversion: str = "1.0"
    datacontenttype: str = "application/json"
    correlation_id: UUID | None = None
    causation_id: UUID | None = None
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        if not _NAME.fullmatch(self.type) or not _NAME.fullmatch(self.source):
            raise ValueError("type and source must be safe CloudEvents names")
        if self.time.tzinfo is None:
            raise ValueError("time must be timezone-aware")
        if self.idempotency_key is not None and not self.idempotency_key.strip():
            raise ValueError("idempotency_key cannot be blank")
        object.__setattr__(self, "data", MappingProxyType(dict(self.data)))

    def to_dict(self) -> dict[str, object]:
        result = {"specversion": self.specversion, "type": self.type, "source": self.source,
                  "id": str(self.id), "time": self.time.isoformat(), "datacontenttype": self.datacontenttype,
                  "data": self.data}
        for key, value in (("subject", self.subject), ("producer", self.producer), ("correlationid", self.correlation_id),
                           ("causationid", self.causation_id), ("idempotencykey", self.idempotency_key)):
            if value is not None: result[key] = str(value)
        return result

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "Envelope":
        allowed = {"specversion","type","source","id","time","datacontenttype","data","subject","producer","correlationid","causationid","idempotencykey"}
        unknown = set(value) - allowed
        if unknown: raise ValueError(f"unknown envelope fields: {sorted(unknown)}")
        required = {"type","source","id","time","data"}
        if not required <= value.keys(): raise ValueError("missing envelope fields")
        return cls(type=str(value["type"]), source=str(value["source"]), data=dict(value["data"]),
                   subject=value.get("subject"), producer=value.get("producer"), id=UUID(str(value["id"])), time=datetime.fromisoformat(str(value["time"])),
                   correlation_id=UUID(str(value["correlationid"])) if value.get("correlationid") else None,
                   causation_id=UUID(str(value["causationid"])) if value.get("causationid") else None,
                   idempotency_key=value.get("idempotencykey"))
