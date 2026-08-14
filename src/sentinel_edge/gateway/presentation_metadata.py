"""Non-authoritative presentation metadata boundary."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PresentationMetadata:
    label: str
    profile: str
    caveats: tuple[str, ...] = ()


def apply_presentation_metadata(authoritative_state: dict[str, Any], metadata: PresentationMetadata) -> dict[str, Any]:
    """Return display metadata separately; never copy client fields into state."""
    if not metadata.label.strip() or not metadata.profile.strip():
        raise ValueError("presentation metadata requires label and profile")
    return {"authoritative_state": dict(authoritative_state), "presentation": {"label": metadata.label, "profile": metadata.profile, "caveats": list(metadata.caveats), "authoritative": False}}
