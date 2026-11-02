"""SQLite connection management with durability and integrity pragmas.

Single writer connection guarded by an RLock (desktop app, serialized writes).
WAL allows concurrent readers via separate read connections for background workers.
All multi-statement writes run inside explicit transactions.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from vybora.core.errors import DatabaseError, friendly_db_message

PRAGMAS = {
    "journal_mode": "WAL",
    "foreign_keys": "ON",
    "synchronous": "FULL",
    "busy_timeout": "5000",
    "temp_store": "MEMORY",
}


class Database:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self._lock = threading.RLock()
        self._conn: sqlite3.Connection | None = None
        self._tx_depth = 0

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
            self._conn.row_factory = sqlite3.Row
            for k, v in PRAGMAS.items():
                self._conn.execute(f"PRAGMA {k}={v}")
        return self._conn

    @property
    def conn(self) -> sqlite3.Connection:
        return self.connect()

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def read_connection(self) -> sqlite3.Connection:
        """Separate read-only-ish connection for background workers (WAL reader)."""
        c = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA busy_timeout=5000")
        c.execute("PRAGMA query_only=ON")
        return c

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Atomic write transaction. Nested calls reuse the outer transaction."""
        with self._lock:
            conn = self.connect()
            outer = self._tx_depth == 0
            if outer:
                conn.execute("BEGIN IMMEDIATE")
            self._tx_depth += 1
            try:
                yield conn
            except Exception as exc:
                self._tx_depth -= 1
                if outer:
                    conn.execute("ROLLBACK")
                if isinstance(exc, sqlite3.Error):
                    raise DatabaseError(friendly_db_message(exc), detail=str(exc)) from exc
                raise
            else:
                self._tx_depth -= 1
                if outer:
                    conn.execute("COMMIT")

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        with self._lock:
            try:
                return self.conn.execute(sql, params)
            except sqlite3.Error as exc:
                raise DatabaseError(friendly_db_message(exc), detail=str(exc)) from exc

    def query(self, sql: str, params: tuple | dict = ()) -> list[sqlite3.Row]:
        with self._lock:
            try:
                return self.conn.execute(sql, params).fetchall()
            except sqlite3.Error as exc:
                raise DatabaseError(friendly_db_message(exc), detail=str(exc)) from exc

    def query_one(self, sql: str, params: tuple | dict = ()) -> sqlite3.Row | None:
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def scalar(self, sql: str, params: tuple | dict = ()) -> Any:
        row = self.query_one(sql, params)
        return row[0] if row is not None else None
