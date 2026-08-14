"""Identifier classification: IDs identify records but never grant authority."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class IdentifierKind(StrEnum):
    CORRELATION = "correlation"
    SORTABLE_PUBLIC = "sortable_public"
    DATABASE = "database"
    CONTENT = "content"


@dataclass(frozen=True)
class IdentifierRef:
    kind: IdentifierKind
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("identifier value is required")

    def grants_capability(self) -> bool:
        return False


def authorize_by_identifier(identifier: IdentifierRef) -> bool:
    """Capability checks must use principal/permission state, never identifier possession."""
    return False
