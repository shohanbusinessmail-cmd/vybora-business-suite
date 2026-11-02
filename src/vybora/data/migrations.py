"""Ordered, transactional schema migrations with checksum verification.

Each NNNN_name.sql runs in one transaction and is recorded in schema_migrations.
Applied migrations are checksum-verified on startup (tamper/drift detection).
The app refuses to start on downgrade or checksum mismatch. Failure rolls back fully.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
from pathlib import Path

from vybora.core.errors import DatabaseError
from vybora.data.db import Database


def _iter_statements(sql: str):
    """Yield complete SQL statements, correctly handling triggers/BEGIN...END."""
    buf = ""
    for line in sql.splitlines(keepends=True):
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        buf += line
        if sqlite3.complete_statement(buf):
            stmt = buf.strip()
            if stmt:
                yield stmt
            buf = ""
    if buf.strip():
        yield buf.strip()


MIGRATIONS_DIR = Path(__file__).parent / "migrations"
_FILE_RE = re.compile(r"^(\d{4})_[a-z0-9_]+\.sql$")


def _migration_files() -> list[tuple[int, str, Path]]:
    out = []
    for p in sorted(MIGRATIONS_DIR.glob("*.sql")):
        m = _FILE_RE.match(p.name)
        if not m:
            raise DatabaseError(f"মাইগ্রেশন ফাইলের নাম অবৈধ: {p.name}")
        out.append((int(m.group(1)), p.name, p))
    return out


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def migrate(db: Database) -> int:
    """Apply pending migrations; return the resulting schema version."""
    with db.transaction() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS schema_migrations (
                   version INTEGER PRIMARY KEY,
                   name TEXT NOT NULL,
                   checksum TEXT NOT NULL,
                   applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
               )"""
        )
        applied = {row["version"]: row for row in conn.execute("SELECT * FROM schema_migrations")}
        files = _migration_files()
        if not files:
            raise DatabaseError("কোনো মাইগ্রেশন ফাইল পাওয়া যায়নি।")
        max_applied = max(applied) if applied else 0
        max_file = files[-1][0]
        if max_applied > max_file:
            raise DatabaseError("ডেটাবেস সংস্করণ অ্যাপের চেয়ে নতুন। অনুগ্রহ করে অ্যাপ আপডেট করুন।")
        for version, name, path in files:
            checksum = _sha256(path)
            if version in applied:
                if applied[version]["checksum"] != checksum:
                    raise DatabaseError(f"মাইগ্রেশন ফাইল পরিবর্তিত হয়েছে: {name}")
                continue
            sql = path.read_text(encoding="utf-8")
            for stmt in _iter_statements(sql):
                conn.execute(stmt)
            conn.execute(
                "INSERT INTO schema_migrations (version, name, checksum) VALUES (?,?,?)",
                (version, name, checksum),
            )
    return max_file


def current_version(db: Database) -> int:
    row = db.query_one("SELECT MAX(version) AS v FROM schema_migrations")
    return int(row["v"]) if row and row["v"] is not None else 0
