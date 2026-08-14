"""Persistent globally ordered authority-journal positions."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthorityPosition:
    epoch: int
    ordinal: int
    sequence: int
    predecessor: tuple[int, int, int] | None


class AuthorityJournal:
    def __init__(self) -> None:
        self._positions: list[AuthorityPosition] = []

    def accept(self) -> AuthorityPosition:
        previous = self._positions[-1] if self._positions else None
        position = AuthorityPosition(1, len(self._positions) + 1, len(self._positions) + 1, (previous.epoch, previous.ordinal, previous.sequence) if previous else None)
        self._positions.append(position)
        return position

    def verify(self) -> bool:
        return all(item.ordinal == index and item.sequence == index and (index == 1 or item.predecessor == (self._positions[index - 2].epoch, self._positions[index - 2].ordinal, self._positions[index - 2].sequence)) for index, item in enumerate(self._positions, 1))
