from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import RLock
from typing import Callable

from sentinel_edge.domain.models import AnalysisResult


class SpoolExhaustedError(RuntimeError):
    pass


@dataclass(frozen=True)
class SpoolMetrics:
    pending_items: int
    pending_bytes: int
    maximum_items: int
    maximum_bytes: int
    oldest_age_seconds: float
    expired_items: int
    exhausted: bool


class CriticalAnalysisSpool:
    """Persistent bounded spool used only while Component 4 is unavailable.

    Exhaustion is explicit. No pending item is overwritten or silently discarded.
    """

    def __init__(
        self,
        path: str | Path = ":memory:",
        *,
        max_items: int = 256,
        max_bytes: int = 4 * 1024 * 1024,
        max_age_seconds: int = 900,
    ) -> None:
        if max_items <= 0 or max_bytes <= 0 or max_age_seconds <= 0:
            raise ValueError("spool bounds must be positive")
        self.path = str(path)
        self.max_items = max_items
        self.max_bytes = max_bytes
        self.max_age_seconds = max_age_seconds
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=FULL")
        self._lock = RLock()
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS pending_analysis (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id TEXT NOT NULL UNIQUE,
                hazard TEXT NOT NULL,
                enqueued_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                payload_bytes INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS spool_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id TEXT NOT NULL,
                status TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                reason TEXT,
                payload_bytes INTEGER NOT NULL
            );
            """
        )
        self._connection.commit()

    def _counts(self) -> tuple[int, int]:
        row = self._connection.execute(
            "SELECT COUNT(*), COALESCE(SUM(payload_bytes),0) FROM pending_analysis"
        ).fetchone()
        return int(row[0]), int(row[1])

    def enqueue(self, analysis: AnalysisResult, *, enqueued_at: datetime | None = None) -> bool:
        enqueued_at = enqueued_at or datetime.now(timezone.utc)
        payload = analysis.model_dump_json()
        payload_bytes = len(payload.encode("utf-8"))
        expires_at = enqueued_at + timedelta(seconds=self.max_age_seconds)
        exhausted = False
        with self._lock, self._connection:
            existing = self._connection.execute(
                "SELECT payload_json FROM pending_analysis WHERE analysis_id=?", (str(analysis.analysis_id),)
            ).fetchone()
            if existing is not None:
                if existing[0] != payload:
                    raise ValueError("analysis spool identity conflict")
                return False
            items, total_bytes = self._counts()
            if items + 1 > self.max_items or total_bytes + payload_bytes > self.max_bytes:
                self._connection.execute(
                    "INSERT INTO spool_events(analysis_id,status,recorded_at,reason,payload_bytes) VALUES (?,?,?,?,?)",
                    (str(analysis.analysis_id), "rejected", enqueued_at.isoformat(), "spool_exhausted", payload_bytes),
                )
                exhausted = True
            else:
                self._connection.execute(
                """
                INSERT INTO pending_analysis(analysis_id,hazard,enqueued_at,expires_at,payload_json,payload_bytes)
                VALUES (?,?,?,?,?,?)
                """,
                (
                    str(analysis.analysis_id), analysis.hazard.value, enqueued_at.isoformat(), expires_at.isoformat(),
                    payload, payload_bytes,
                ),
            )
            self._connection.execute(
                "INSERT INTO spool_events(analysis_id,status,recorded_at,reason,payload_bytes) VALUES (?,?,?,?,?)",
                    (str(analysis.analysis_id), "enqueued", enqueued_at.isoformat(), None, payload_bytes),
                )
        if exhausted:
            raise SpoolExhaustedError("critical analysis spool exhausted")
        return True

    def pending(self) -> tuple[AnalysisResult, ...]:
        rows = self._connection.execute(
            "SELECT payload_json FROM pending_analysis ORDER BY sequence"
        ).fetchall()
        return tuple(AnalysisResult.model_validate_json(row[0]) for row in rows)

    def drain(
        self,
        handler: Callable[[AnalysisResult], object],
        *,
        now: datetime | None = None,
    ) -> tuple[str, ...]:
        now = now or datetime.now(timezone.utc)
        delivered: list[str] = []
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM pending_analysis ORDER BY sequence"
            ).fetchall()
            for row in rows:
                analysis = AnalysisResult.model_validate_json(row["payload_json"])
                analysis_id = str(analysis.analysis_id)
                expires_at = datetime.fromisoformat(row["expires_at"])
                if expires_at <= now:
                    with self._connection:
                        self._connection.execute(
                            "INSERT INTO spool_events(analysis_id,status,recorded_at,reason,payload_bytes) VALUES (?,?,?,?,?)",
                            (analysis_id, "expired", now.isoformat(), "maximum_age_exceeded", row["payload_bytes"]),
                        )
                    # Expired critical evidence remains pending until an operator or reconciliation policy handles it.
                    break
                try:
                    handler(analysis)
                except Exception as exc:
                    with self._connection:
                        self._connection.execute(
                            "INSERT INTO spool_events(analysis_id,status,recorded_at,reason,payload_bytes) VALUES (?,?,?,?,?)",
                            (analysis_id, "delivery_failed", now.isoformat(), type(exc).__name__, row["payload_bytes"]),
                        )
                    break
                with self._connection:
                    self._connection.execute("DELETE FROM pending_analysis WHERE analysis_id=?", (analysis_id,))
                    self._connection.execute(
                        "INSERT INTO spool_events(analysis_id,status,recorded_at,reason,payload_bytes) VALUES (?,?,?,?,?)",
                        (analysis_id, "delivered", now.isoformat(), None, row["payload_bytes"]),
                    )
                delivered.append(analysis_id)
        return tuple(delivered)

    def metrics(self, *, now: datetime | None = None) -> SpoolMetrics:
        now = now or datetime.now(timezone.utc)
        items, total_bytes = self._counts()
        oldest = self._connection.execute("SELECT MIN(enqueued_at) FROM pending_analysis").fetchone()[0]
        oldest_age = max(0.0, (now - datetime.fromisoformat(oldest)).total_seconds()) if oldest else 0.0
        expired = self._connection.execute(
            "SELECT COUNT(*) FROM pending_analysis WHERE expires_at <= ?", (now.isoformat(),)
        ).fetchone()[0]
        return SpoolMetrics(
            pending_items=items,
            pending_bytes=total_bytes,
            maximum_items=self.max_items,
            maximum_bytes=self.max_bytes,
            oldest_age_seconds=oldest_age,
            expired_items=int(expired),
            exhausted=items >= self.max_items or total_bytes >= self.max_bytes,
        )

    def events(self) -> tuple[dict[str, object], ...]:
        rows = self._connection.execute("SELECT * FROM spool_events ORDER BY event_id").fetchall()
        return tuple(dict(row) for row in rows)

    def close(self) -> None:
        self._connection.close()
