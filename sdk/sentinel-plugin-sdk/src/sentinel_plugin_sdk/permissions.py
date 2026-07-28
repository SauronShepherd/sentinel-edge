from dataclasses import dataclass
from typing import FrozenSet

@dataclass(frozen=True, slots=True)
class Permissions:
    network: FrozenSet[str] = frozenset()
    filesystem: FrozenSet[str] = frozenset()
    secrets: FrozenSet[str] = frozenset()
    artifacts: FrozenSet[str] = frozenset()
    models: FrozenSet[str] = frozenset()
    def __post_init__(self) -> None:
        values = self.network | self.filesystem | self.secrets | self.artifacts | self.models
        if "*" in values: raise ValueError("wildcard permissions are forbidden")
        if any("incident" in v.lower() for v in self.filesystem | self.artifacts): raise ValueError("incident authority is forbidden")
