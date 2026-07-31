from pathlib import Path
import hashlib
import time

class QuarantineFile:
    def __init__(self, root: str | Path, max_bytes: int = 10_000_000, retention_seconds: int = 86_400):
        self.root, self.max_bytes, self.retention_seconds = Path(root), max_bytes, retention_seconds; self.root.mkdir(parents=True, exist_ok=True)
    def store(self, content: bytes) -> Path:
        if len(content) > self.max_bytes: raise ValueError("quarantine_size_limit")
        digest = hashlib.sha256(content).hexdigest(); target = self.root / digest
        if not target.exists(): target.write_bytes(content)
        return target
    def purge(self, now: float | None = None) -> int:
        now = now or time.time(); removed = 0
        for item in self.root.iterdir():
            if item.is_file() and now - item.stat().st_mtime > self.retention_seconds: item.unlink(); removed += 1
        return removed

