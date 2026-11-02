"""Transaction-safe document numbering.

Must be called inside an active write transaction. UPDATE ... RETURNING atomically
allocates the next value; a rolled-back transaction returns the number to the pool
(no gaps from failures, no duplicates under the serialized writer).
"""

from __future__ import annotations

import sqlite3

from vybora.core.errors import DatabaseError
from vybora.domain.numbering import format_number


def next_document_number(conn: sqlite3.Connection, name: str) -> str:
    row = conn.execute(
        "UPDATE sequences SET next_value = next_value + 1 WHERE name = ? "
        "RETURNING prefix, next_value - 1 AS allocated, padding",
        (name,),
    ).fetchone()
    if row is None:
        raise DatabaseError(f"অজানা ডকুমেন্ট সিকোয়েন্স: {name}")
    return format_number(row["prefix"], row["allocated"], row["padding"])
