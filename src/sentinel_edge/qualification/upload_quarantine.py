"""Component-1-owned streaming quarantine with bounded chunks."""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path


class QuarantineStream:
    def __init__(self, root: str | Path, *, max_chunk_bytes: int = 64 * 1024) -> None:
        self.root = Path(root).resolve()
        self.quarantine = self.root / ".quarantine"
        self.quarantine.mkdir(parents=True, exist_ok=True)
        self.max_chunk_bytes = max_chunk_bytes
        self._file = None
        self._path: Path | None = None
        self._hash = hashlib.sha256()
        self.bytes_count = 0

    def begin(self) -> None:
        if self._file is not None:
            raise RuntimeError("quarantine_stream_active")
        handle, name = tempfile.mkstemp(prefix=".tmp-upload-", dir=self.quarantine)
        self._file, self._path = os.fdopen(handle, "wb"), Path(name)

    def write(self, chunk: bytes) -> None:
        if self._file is None:
            raise RuntimeError("quarantine_stream_not_started")
        if len(chunk) > self.max_chunk_bytes:
            raise ValueError("backpressure_chunk_limit_exceeded")
        self._file.write(chunk)
        self._hash.update(chunk)
        self.bytes_count += len(chunk)

    def abort(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None
        if self._path is not None:
            self._path.unlink(missing_ok=True)
            self._path = None

    def complete(self) -> tuple[Path, str]:
        if self._file is None or self._path is None:
            raise RuntimeError("quarantine_stream_not_started")
        self._file.flush()
        os.fsync(self._file.fileno())
        self._file.close()
        self._file = None
        final = self.quarantine / (self._hash.hexdigest() + ".upload")
        os.replace(self._path, final)
        self._path = None
        return final, self._hash.hexdigest()
