"""Bounded I/O workload expectations for registry and admission."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IoWorkloadExpectation:
    workload_id: str
    io_class: str
    criticality: str
    read_bytes_limit: int
    write_bytes_limit: int
    fsync_required: bool
    temporary_space_bytes_limit: int
    durability: str

    def __post_init__(self) -> None:
        if not self.workload_id.strip() or not self.io_class.strip() or not self.criticality.strip() or not self.durability.strip():
            raise ValueError("I/O workload identity and classes are required")
        if min(self.read_bytes_limit, self.write_bytes_limit, self.temporary_space_bytes_limit) < 0:
            raise ValueError("I/O limits cannot be negative")

    def registry_record(self) -> dict[str, object]:
        return {"workload_id": self.workload_id, "io_class": self.io_class, "criticality": self.criticality, "read_bytes_limit": self.read_bytes_limit, "write_bytes_limit": self.write_bytes_limit, "fsync_required": self.fsync_required, "temporary_space_bytes_limit": self.temporary_space_bytes_limit, "durability": self.durability}
