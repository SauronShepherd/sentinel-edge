"""Fail-closed labels for imported or reconstructed history."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HistorySequence:
    entries: tuple[dict[str, object], ...]
    exact_authority_positions: bool

    @property
    def state(self) -> str:
        return "original" if self.exact_authority_positions else "reconstructed_incomplete"

    def as_metadata(self) -> dict[str, object]:
        return {
            "history_state": self.state,
            "exact_authority_positions": self.exact_authority_positions,
            "entry_count": len(self.entries),
        }


def import_history(entries: list[dict[str, object]], *, exact_authority_positions: bool) -> HistorySequence:
    """Import history without allowing uncertain ordering to masquerade as original."""
    return HistorySequence(tuple(dict(entry) for entry in entries), exact_authority_positions)
