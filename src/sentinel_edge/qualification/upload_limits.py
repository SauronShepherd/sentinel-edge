"""Bounded streaming upload admission and hashing."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class UploadLimits:
    max_bytes: int = 8 * 1024 * 1024
    max_seconds: float = 30.0
    allowed_media_classes: tuple[str, ...] = ("image", "audio", "text")
    max_concurrent: int = 2
    max_storage_bytes: int = 64 * 1024 * 1024


@dataclass(frozen=True)
class UploadResult:
    accepted: bool
    code: str
    bytes_count: int
    sha256: str


class StreamingUploadLimiter:
    def __init__(self, limits: UploadLimits, *, stored_bytes: int = 0) -> None:
        self.limits = limits
        self.stored_bytes = stored_bytes
        self._active = 0

    def begin(self, *, media_class: str, started_at: float) -> "UploadSession":
        if media_class not in self.limits.allowed_media_classes:
            raise ValueError("media_class_not_allowed")
        if self._active >= self.limits.max_concurrent:
            raise RuntimeError("concurrency_quota_exceeded")
        self._active += 1
        return UploadSession(self, media_class, started_at)

    def _finish(self) -> None:
        self._active = max(0, self._active - 1)


class UploadSession:
    def __init__(self, owner: StreamingUploadLimiter, media_class: str, started_at: float) -> None:
        self.owner, self.media_class, self.started_at = owner, media_class, started_at
        self._hash = hashlib.sha256()
        self._bytes = 0
        self._closed = False

    def write(self, chunk: bytes, *, now: float) -> None:
        if self._closed:
            raise RuntimeError("upload_session_closed")
        if now - self.started_at > self.owner.limits.max_seconds:
            raise ValueError("time_quota_exceeded")
        if self._bytes + len(chunk) > self.owner.limits.max_bytes:
            raise ValueError("byte_quota_exceeded")
        projected = self.owner.stored_bytes + self._bytes + len(chunk)
        if projected > self.owner.limits.max_storage_bytes:
            raise ValueError("storage_quota_exceeded")
        self._hash.update(chunk)
        self._bytes += len(chunk)

    def finish(self, *, now: float) -> UploadResult:
        try:
            if now - self.started_at > self.owner.limits.max_seconds:
                return UploadResult(False, "time_quota_exceeded", self._bytes, self._hash.hexdigest())
            self.owner.stored_bytes += self._bytes
            return UploadResult(True, "accepted", self._bytes, self._hash.hexdigest())
        finally:
            self._closed = True
            self.owner._finish()
