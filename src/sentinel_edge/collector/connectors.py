from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Callable

from sentinel_edge.collector.references import validate_reference
from sentinel_edge.domain.models import SourceMode


class ConnectorState(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    DRAINING = "draining"
    STOPPED = "stopped"
    FAILED = "failed"


class ConnectorMode(StrEnum):
    POLL = "poll"
    SUBSCRIBE = "subscribe"
    WEBHOOK = "webhook"
    STREAM = "stream"
    FIXTURE = "fixture"


@dataclass(frozen=True)
class ConnectorShutdownReceipt:
    connector_id: str
    state: ConnectorState
    accepted_items: int
    processed_items: int
    cancelled_items: int
    thread_alive: bool
    stopped_at: datetime
    deadline_seconds: float
    reason_codes: tuple[str, ...]


class BoundedBackgroundConnector:
    """Fake-transport connector used to enforce drain/stop lifecycle contracts.

    It is intentionally transport-agnostic. Real connectors must implement the same
    bounded acceptance, drain, deadline, and no-receive-after-stop semantics.
    """

    def __init__(
        self,
        connector_id: str,
        handler: Callable[[Any], None],
        *,
        queue_limit: int = 64,
        source_mode: SourceMode = SourceMode.FIXTURE,
        allowed_hosts: frozenset[str] = frozenset(),
        connector_mode: ConnectorMode = ConnectorMode.FIXTURE,
        normalizer: Callable[[Any], Any] | None = None,
    ) -> None:
        if queue_limit <= 0:
            raise ValueError("connector queue_limit must be positive")
        self.connector_id = connector_id
        self.handler = handler
        self.source_mode = source_mode
        self.allowed_hosts = allowed_hosts
        self.connector_mode = connector_mode
        self.normalizer = normalizer or (lambda item: item)
        self._queue: queue.Queue[Any] = queue.Queue(maxsize=queue_limit)
        self._state = ConnectorState.CREATED
        self._state_lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._accepted = 0
        self._processed = 0
        self._cancelled = 0

    @property
    def state(self) -> ConnectorState:
        with self._state_lock:
            return self._state

    def start(self) -> None:
        with self._state_lock:
            if self._state is not ConnectorState.CREATED:
                raise RuntimeError("connector can start only once")
            self._state = ConnectorState.RUNNING
            self._thread = threading.Thread(target=self._run, name=f"sentinel-connector-{self.connector_id}", daemon=True)
            self._thread.start()

    def submit(self, item: Any, *, timeout_seconds: float = 0.1) -> None:
        with self._state_lock:
            if self._state is not ConnectorState.RUNNING:
                raise RuntimeError("connector is not accepting new input")
        try:
            normalized = self.normalizer(item)
        except Exception as exc:
            raise ValueError("connector normalization rejected input") from exc
        self._queue.put(normalized, timeout=timeout_seconds)
        self._accepted += 1

    def submit_reference(self, value: str, *, timeout_seconds: float = 0.1) -> None:
        """Admit a URL only through the declared source policy boundary."""
        decision = validate_reference(
            value,
            permit_resolution=self.source_mode is SourceMode.LIVE,
            allowed_hosts=self.allowed_hosts,
        )
        if decision.state != "resolution_permitted":
            raise ValueError("external reference rejected: " + ",".join(decision.reason_codes))
        self.submit(decision.canonical_url, timeout_seconds=timeout_seconds)

    def _run(self) -> None:
        try:
            while True:
                if self._stop.is_set() and self._queue.empty():
                    break
                try:
                    item = self._queue.get(timeout=0.02)
                except queue.Empty:
                    continue
                try:
                    self.handler(item)
                    self._processed += 1
                finally:
                    self._queue.task_done()
        except BaseException:
            with self._state_lock:
                self._state = ConnectorState.FAILED
            raise
        finally:
            with self._state_lock:
                if self._state is not ConnectorState.FAILED:
                    self._state = ConnectorState.STOPPED

    def drain_and_stop(self, *, deadline_seconds: float) -> ConnectorShutdownReceipt:
        if deadline_seconds <= 0:
            raise ValueError("shutdown deadline must be positive")
        started = time.monotonic()
        with self._state_lock:
            if self._state is ConnectorState.STOPPED:
                thread_alive = bool(self._thread and self._thread.is_alive())
                return ConnectorShutdownReceipt(
                    self.connector_id, self._state, self._accepted, self._processed, self._cancelled,
                    thread_alive, datetime.now(timezone.utc), deadline_seconds, ("already_stopped",),
                )
            if self._state not in {ConnectorState.RUNNING, ConnectorState.DRAINING}:
                raise RuntimeError("connector is not running")
            self._state = ConnectorState.DRAINING
        while not self._queue.empty() and time.monotonic() - started < deadline_seconds:
            time.sleep(0.005)
        reason_codes: list[str] = []
        if not self._queue.empty():
            while True:
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break
                else:
                    self._queue.task_done()
                    self._cancelled += 1
            reason_codes.append("deadline_reached_pending_items_cancelled")
        else:
            reason_codes.append("queue_drained")
        self._stop.set()
        remaining = max(0.0, deadline_seconds - (time.monotonic() - started))
        if self._thread is not None:
            self._thread.join(timeout=remaining)
        thread_alive = bool(self._thread and self._thread.is_alive())
        if thread_alive:
            reason_codes.append("worker_thread_failed_to_stop_within_deadline")
            with self._state_lock:
                self._state = ConnectorState.FAILED
        else:
            with self._state_lock:
                self._state = ConnectorState.STOPPED
        return ConnectorShutdownReceipt(
            connector_id=self.connector_id,
            state=self.state,
            accepted_items=self._accepted,
            processed_items=self._processed,
            cancelled_items=self._cancelled,
            thread_alive=thread_alive,
            stopped_at=datetime.now(timezone.utc),
            deadline_seconds=deadline_seconds,
            reason_codes=tuple(reason_codes),
        )
