import sqlite3
from pathlib import Path

class SQLiteRepository:
    def __init__(self, path: str | Path = ":memory:"):
        self.connection = sqlite3.connect(str(path))
        self.connection.execute("CREATE TABLE IF NOT EXISTS ingress (identity TEXT PRIMARY KEY, payload BLOB NOT NULL, state TEXT NOT NULL)")
        self.connection.commit()
    def record(self, identity: str, payload: bytes, state: str = "durable") -> bool:
        cur = self.connection.execute("INSERT OR IGNORE INTO ingress VALUES (?, ?, ?)", (identity, payload, state)); self.connection.commit(); return cur.rowcount == 1
    def contains(self, identity: str) -> bool:
        return self.connection.execute("SELECT 1 FROM ingress WHERE identity=?", (identity,)).fetchone() is not None
    def close(self) -> None: self.connection.close()

