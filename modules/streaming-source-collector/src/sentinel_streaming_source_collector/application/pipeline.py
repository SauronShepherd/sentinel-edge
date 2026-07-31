from collections.abc import Callable, Iterable
from ..domain.deduplication import decide, identity
from ..adapters.sqlite_repository import SQLiteRepository
from ..diagnostics.metrics import Metrics

class CollectorPipeline:
    def __init__(self, repository: SQLiteRepository, capacity: int = 100, metrics: Metrics | None = None):
        if capacity < 1: raise ValueError("capacity_must_be_positive")
        self.repository, self.capacity, self.metrics = repository, capacity, metrics or Metrics()
    def ingest(self, source_id: str, records: Iterable[tuple[int | str, bytes]], emit: Callable[[bytes], None]) -> int:
        accepted = 0
        for sequence, payload in records:
            key = identity(source_id, sequence, payload)
            if decide(key, set()).action == "accept" and self.repository.record(key, payload):
                emit(payload); accepted += 1; self.metrics.increment("accepted")
            else: self.metrics.increment("duplicates")
        return accepted

