"""Pinned transform environment manifest."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TransformEnvironmentPin:
    pyproj_version: str
    proj_version: str
    proj_db_sha256: str
    grid_digests: tuple[str, ...]
    transform_policy: str
    environment_digest: str

    def __post_init__(self) -> None:
        if any(not value.strip() for value in (self.pyproj_version, self.proj_version, self.proj_db_sha256, self.transform_policy, self.environment_digest)):
            raise ValueError("transform environment pin is incomplete")
        if len(self.proj_db_sha256) != 64 or len(self.environment_digest) != 64:
            raise ValueError("transform environment digests must be SHA-256")
        if any(len(value) != 64 for value in self.grid_digests):
            raise ValueError("grid digests must be SHA-256")

    def as_dict(self) -> dict[str, object]:
        return {"pyproj_version": self.pyproj_version, "proj_version": self.proj_version, "proj_db_sha256": self.proj_db_sha256, "grid_digests": list(self.grid_digests), "transform_policy": self.transform_policy, "environment_digest": self.environment_digest}
