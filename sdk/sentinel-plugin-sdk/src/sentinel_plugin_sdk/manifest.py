from dataclasses import dataclass
from typing import FrozenSet
import re
from .permissions import Permissions

PermissionSet = Permissions

@dataclass(frozen=True, slots=True)
class Manifest:
    name: str
    version: str
    api_version: str
    digest: str
    permissions: PermissionSet
    modes: frozenset[str]
    contracts: frozenset[str]
    max_memory_mb: int
    max_cpu_ms: int
    fixtures: frozenset[str] = frozenset()
    dependencies: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.name or not re.fullmatch(r"sha256:[0-9a-f]{64}", self.digest): raise ValueError("invalid identity or digest")
        if self.max_memory_mb <= 0 or self.max_cpu_ms <= 0: raise ValueError("resources must be bounded")
        if not self.modes or "incident-writer" in self.modes: raise ValueError("invalid plugin authority")

    @classmethod
    def from_dict(cls, value: dict) -> "Manifest":
        budget = value.get("budgets", {})
        return cls(name=value["name"], version=value["version"], api_version=value["api_version"], digest=value["digest"],
                   permissions=PermissionSet(**{k: frozenset(v) for k,v in value.get("permissions", {}).items()}),
                   modes=frozenset(value.get("modes", [])), contracts=frozenset(value.get("contracts", [])),
                   max_memory_mb=int(budget.get("max_memory_mb", 0)), max_cpu_ms=int(budget.get("max_cpu_ms", 0)),
                   fixtures=frozenset(value.get("fixtures", [])), dependencies=frozenset(value.get("dependencies", [])))
