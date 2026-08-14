"""Bounded in-memory repository for the optional collaboration demo path.

The repository stores only already-minimized Component-1 envelopes and
Component-4 correlation decisions; it never stores raw MIME or sensor streams.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from .models import CollaborativeSignalEnvelope, CorrelationDecisionRecord


@dataclass
class CollaborationRepository:
    max_envelopes: int = 512
    max_decisions: int = 512
    _envelopes: deque[CollaborativeSignalEnvelope] = field(default_factory=deque, init=False)
    _decisions: deque[CorrelationDecisionRecord] = field(default_factory=deque, init=False)
    _signal_ids: set[str] = field(default_factory=set, init=False)

    def add_envelope(self, envelope: CollaborativeSignalEnvelope) -> bool:
        if envelope.signal.signal_id in self._signal_ids:
            return False
        while len(self._envelopes) >= self.max_envelopes:
            evicted = self._envelopes.popleft()
            self._signal_ids.discard(evicted.signal.signal_id)
        self._envelopes.append(envelope)
        self._signal_ids.add(envelope.signal.signal_id)
        return True

    def add_decision(self, decision: CorrelationDecisionRecord) -> None:
        while len(self._decisions) >= self.max_decisions:
            self._decisions.popleft()
        self._decisions.append(decision)

    def episode_envelopes(self, envelope: CollaborativeSignalEnvelope) -> list[CollaborativeSignalEnvelope]:
        signal = envelope.signal
        return [
            item for item in self._envelopes
            if item.signal.hazard == signal.hazard
            and item.signal.correlation_domain.kind == signal.correlation_domain.kind
            and item.signal.correlation_domain.id == signal.correlation_domain.id
        ]

    def envelopes(self) -> tuple[CollaborativeSignalEnvelope, ...]:
        return tuple(self._envelopes)

    def decisions(self) -> tuple[CorrelationDecisionRecord, ...]:
        return tuple(self._decisions)

    def purge_expired(self, now: datetime | None = None) -> int:
        now = now or datetime.now(timezone.utc)
        kept = deque(item for item in self._envelopes if item.signal.expires_at > now)
        removed = len(self._envelopes) - len(kept)
        self._envelopes = kept
        self._signal_ids = {item.signal.signal_id for item in kept}
        return removed


class SqliteCollaborationRepository:
    """Optional module-owned durable Component-4 collaboration repository.

    It persists only normalized/minimized envelopes and correlation decisions.
    Raw Gmail MIME and local sensor/media evidence are intentionally outside
    this store.  The in-memory repository remains the deterministic fixture
    default so H0 startup has no new persistence dependency.
    """

    def __init__(self, path: str, *, max_envelopes: int = 4096, max_decisions: int = 4096) -> None:
        import sqlite3
        from pathlib import Path

        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.max_envelopes = max_envelopes
        self.max_decisions = max_decisions
        self._sqlite3 = sqlite3
        with self._connect() as db:
            db.executescript(
                """
                PRAGMA journal_mode=WAL;
                PRAGMA foreign_keys=ON;
                CREATE TABLE IF NOT EXISTS collaborative_inbound_signals (
                    signal_id TEXT PRIMARY KEY,
                    transport TEXT NOT NULL,
                    transport_message_id TEXT NOT NULL UNIQUE,
                    received_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    hazard TEXT NOT NULL,
                    domain_kind TEXT NOT NULL,
                    domain_id TEXT NOT NULL,
                    node_pseudonym TEXT NOT NULL,
                    validation_state TEXT NOT NULL,
                    serialized_normalized_signal TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS collaboration_episodes (
                    correlation_episode_id TEXT PRIMARY KEY,
                    hazard TEXT NOT NULL,
                    domain_kind TEXT NOT NULL,
                    domain_id TEXT NOT NULL,
                    policy_id TEXT NOT NULL,
                    window_start TEXT NOT NULL,
                    window_end TEXT NOT NULL,
                    state TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS collaboration_contributions (
                    correlation_episode_id TEXT NOT NULL,
                    signal_id TEXT NOT NULL,
                    node_pseudonym TEXT,
                    accepted INTEGER NOT NULL,
                    reason_code TEXT,
                    observed_sequence INTEGER,
                    PRIMARY KEY (correlation_episode_id, signal_id),
                    FOREIGN KEY (correlation_episode_id) REFERENCES collaboration_episodes(correlation_episode_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS collaboration_decisions (
                    decision_id TEXT PRIMARY KEY,
                    correlation_episode_id TEXT NOT NULL,
                    created_or_updated_incident_id TEXT,
                    decision_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (correlation_episode_id) REFERENCES collaboration_episodes(correlation_episode_id) ON DELETE CASCADE
                );
                """
            )

    def _connect(self):
        db = self._sqlite3.connect(self.path, timeout=5)
        db.row_factory = self._sqlite3.Row
        return db

    @staticmethod
    def _json(model) -> str:
        return model.model_dump_json()

    @staticmethod
    def _episode_id(decision: CorrelationDecisionRecord) -> str:
        from hashlib import sha256
        raw = f"{decision.hazard}:{decision.domain_kind}:{decision.domain_id}:{decision.window_start.isoformat()}:{decision.window_end.isoformat()}"
        return "collabep_" + sha256(raw.encode()).hexdigest()[:24]

    def add_envelope(self, envelope: CollaborativeSignalEnvelope) -> bool:
        signal = envelope.signal
        with self._connect() as db:
            try:
                db.execute(
                    """INSERT INTO collaborative_inbound_signals
                    (signal_id, transport, transport_message_id, received_at, expires_at, hazard, domain_kind, domain_id, node_pseudonym, validation_state, serialized_normalized_signal)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        signal.signal_id, envelope.transport, envelope.transport_message_id,
                        envelope.received_at.isoformat(), signal.expires_at.isoformat(), signal.hazard,
                        signal.correlation_domain.kind, signal.correlation_domain.id, signal.node_pseudonym,
                        envelope.validation_state, self._json(envelope),
                    ),
                )
            except self._sqlite3.IntegrityError:
                return False
            excess = db.execute("SELECT COUNT(*) FROM collaborative_inbound_signals").fetchone()[0] - self.max_envelopes
            if excess > 0:
                db.execute(
                    "DELETE FROM collaborative_inbound_signals WHERE signal_id IN (SELECT signal_id FROM collaborative_inbound_signals ORDER BY received_at ASC LIMIT ?)",
                    (excess,),
                )
        return True

    def add_decision(self, decision: CorrelationDecisionRecord) -> None:
        episode_id = self._episode_id(decision)
        accepted = set(decision.accepted_signal_ids)
        with self._connect() as db:
            db.execute(
                """INSERT INTO collaboration_episodes
                (correlation_episode_id, hazard, domain_kind, domain_id, policy_id, window_start, window_end, state)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(correlation_episode_id) DO UPDATE SET window_end=excluded.window_end, state=excluded.state""",
                (
                    episode_id, decision.hazard, decision.domain_kind, decision.domain_id, decision.policy_id,
                    decision.window_start.isoformat(), decision.window_end.isoformat(), decision.selected_action,
                ),
            )
            envelope_by_id = {item.signal.signal_id: item for item in self.envelopes()}
            for signal_id in decision.candidate_signal_ids:
                envelope = envelope_by_id.get(signal_id)
                reason = None
                if signal_id not in accepted:
                    reason = decision.blocking_reasons[0] if decision.blocking_reasons else "REJECTED_BY_POLICY"
                db.execute(
                    """INSERT OR REPLACE INTO collaboration_contributions
                    (correlation_episode_id, signal_id, node_pseudonym, accepted, reason_code, observed_sequence)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        episode_id, signal_id,
                        envelope.signal.node_pseudonym if envelope else None,
                        1 if signal_id in accepted else 0, reason,
                        envelope.signal.sequence if envelope else None,
                    ),
                )
            db.execute(
                """INSERT OR REPLACE INTO collaboration_decisions
                (decision_id, correlation_episode_id, created_or_updated_incident_id, decision_json, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (decision.decision_id, episode_id, decision.created_or_updated_incident_id, self._json(decision), decision.created_at.isoformat()),
            )
            excess = db.execute("SELECT COUNT(*) FROM collaboration_decisions").fetchone()[0] - self.max_decisions
            if excess > 0:
                old_ids = [row[0] for row in db.execute("SELECT decision_id FROM collaboration_decisions ORDER BY created_at ASC LIMIT ?", (excess,)).fetchall()]
                db.executemany("DELETE FROM collaboration_decisions WHERE decision_id=?", [(item,) for item in old_ids])

    def envelopes(self) -> tuple[CollaborativeSignalEnvelope, ...]:
        with self._connect() as db:
            rows = db.execute("SELECT serialized_normalized_signal FROM collaborative_inbound_signals ORDER BY received_at, signal_id").fetchall()
        return tuple(CollaborativeSignalEnvelope.model_validate_json(row[0]) for row in rows)

    def decisions(self) -> tuple[CorrelationDecisionRecord, ...]:
        with self._connect() as db:
            rows = db.execute("SELECT decision_json FROM collaboration_decisions ORDER BY created_at, decision_id").fetchall()
        return tuple(CorrelationDecisionRecord.model_validate_json(row[0]) for row in rows)

    def episode_envelopes(self, envelope: CollaborativeSignalEnvelope) -> list[CollaborativeSignalEnvelope]:
        signal = envelope.signal
        return [
            item for item in self.envelopes()
            if item.signal.hazard == signal.hazard
            and item.signal.correlation_domain.kind == signal.correlation_domain.kind
            and item.signal.correlation_domain.id == signal.correlation_domain.id
        ]

    def purge_expired(self, now: datetime | None = None) -> int:
        now = now or datetime.now(timezone.utc)
        with self._connect() as db:
            before = db.execute("SELECT COUNT(*) FROM collaborative_inbound_signals").fetchone()[0]
            db.execute("DELETE FROM collaborative_inbound_signals WHERE expires_at <= ?", (now.isoformat(),))
            after = db.execute("SELECT COUNT(*) FROM collaborative_inbound_signals").fetchone()[0]
        return before - after
