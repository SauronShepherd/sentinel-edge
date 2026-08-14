"""Observed geospatial runtime identity; package labels are not sufficient."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjRuntimeIdentity:
    pyproj_version: str
    proj_library: str
    data_directory: str
    proj_db_sha256: str
    grid_sha256: tuple[str, ...]

    def __post_init__(self) -> None:
        values = (self.pyproj_version, self.proj_library, self.data_directory, self.proj_db_sha256)
        if any(not value.strip() for value in values):
            raise ValueError("actual PROJ runtime identity is incomplete")
        if len(self.proj_db_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.proj_db_sha256.lower()):
            raise ValueError("proj.db digest must be SHA-256")
        if any(len(value) != 64 or any(c not in "0123456789abcdef" for c in value.lower()) for value in self.grid_sha256):
            raise ValueError("grid digests must be SHA-256")


def qualify_proj_runtime(identity: ProjRuntimeIdentity, *, required_grid_digests: frozenset[str] = frozenset()) -> tuple[bool, tuple[str, ...]]:
    missing = sorted(required_grid_digests - set(identity.grid_sha256))
    return (not missing, tuple(f"required_grid_missing:{value}" for value in missing))
