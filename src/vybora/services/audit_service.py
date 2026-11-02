"""Audit logging. Records actor, action, entity and redacted change details."""

from __future__ import annotations

import json

from vybora.data.db import Database
from vybora.security.session import SessionContext

_SENSITIVE_KEYS = {"password", "password_hash", "passphrase", "secret", "token", "signature"}


def _redact(details: dict | None) -> str | None:
    if details is None:
        return None
    clean = {k: ("[REDACTED]" if k.lower() in _SENSITIVE_KEYS else v) for k, v in details.items()}
    return json.dumps(clean, ensure_ascii=False, default=str)


class AuditService:
    def __init__(self, db: Database):
        self.db = db

    def log(
        self,
        ctx: SessionContext | None,
        action: str,
        *,
        entity_type: str | None = None,
        entity_id: int | None = None,
        details: dict | None = None,
    ) -> None:
        user_id = ctx.user_id if ctx and ctx.user_id > 0 else None
        self.db.execute(
            """INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details_json)
               VALUES (?,?,?,?,?)""",
            (user_id, action, entity_type, entity_id, _redact(details)),
        )

    def recent(self, limit: int = 100) -> list:
        return self.db.query(
            """SELECT a.*, u.username FROM audit_logs a
               LEFT JOIN users u ON u.id = a.user_id
               ORDER BY a.id DESC LIMIT ?""",
            (limit,),
        )
