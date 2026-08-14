"""Bounded reevaluation queue with explicit incomplete outcomes."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from collections import deque


class ReevaluationState(StrEnum):
    QUEUED = "queued"
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    FAILED = "failed"


@dataclass(frozen=True)
class ReevaluationItem:
    item_id: str
    state: ReevaluationState = ReevaluationState.QUEUED
    reason: str = ""


class BoundedReevaluationQueue:
    def __init__(self, capacity: int = 128) -> None:
        if capacity < 1:
            raise ValueError("reevaluation capacity must be positive")
        self.capacity = capacity
        self._items: deque[ReevaluationItem] = deque()

    def enqueue(self, item: ReevaluationItem) -> None:
        if len(self._items) >= self.capacity:
            raise OverflowError("reevaluation queue capacity exhausted")
        if not item.item_id.strip():
            raise ValueError("reevaluation item id is required")
        self._items.append(item)

    def finish(self, item_id: str, *, state: ReevaluationState, reason: str = "") -> ReevaluationItem:
        for index, item in enumerate(self._items):
            if item.item_id == item_id:
                if state is ReevaluationState.QUEUED:
                    raise ValueError("finish state must be terminal")
                result = ReevaluationItem(item.item_id, state, reason)
                self._items[index] = result
                return result
        raise KeyError(item_id)

    def snapshot(self) -> tuple[ReevaluationItem, ...]:
        return tuple(self._items)
