from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetainedClip(Generic[T]):
    frames: tuple[T, ...]
    pre_trigger_count: int
    post_trigger_count: int
    complete: bool


class TriggerClipBuffer(Generic[T]):
    """Bounded deterministic pre/post-trigger clip retention."""

    def __init__(self, *, pre_trigger_frames: int, post_trigger_frames: int) -> None:
        if pre_trigger_frames <= 0 or post_trigger_frames <= 0:
            raise ValueError("clip windows must contain at least one frame")
        self._pre = deque(maxlen=pre_trigger_frames)
        self._post_target = post_trigger_frames
        self._post: list[T] = []
        self._triggered = False

    def append(self, frame: T) -> RetainedClip[T] | None:
        if self._triggered:
            if len(self._post) < self._post_target:
                self._post.append(frame)
            return self.snapshot() if len(self._post) == self._post_target else None
        self._pre.append(frame)
        return None

    def trigger(self) -> None:
        if self._triggered:
            raise ValueError("clip trigger already committed")
        self._triggered = True

    def snapshot(self) -> RetainedClip[T]:
        if not self._triggered:
            raise ValueError("clip has not been triggered")
        return RetainedClip(
            frames=tuple(self._pre) + tuple(self._post),
            pre_trigger_count=len(self._pre),
            post_trigger_count=len(self._post),
            complete=len(self._post) == self._post_target,
        )
