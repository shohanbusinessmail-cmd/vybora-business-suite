"""Authentication: first-run admin setup, login with lockout, sessions, password change."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from vybora.core.errors import ValidationError
from vybora.core.validation import require_non_empty
from vybora.data.db import Database
from vybora.security.passwords import hash_password, needs_rehash, verify_password
from vybora.security.session import SessionContext
from vybora.services.audit_service import AuditService

MAX_FAILED = 5
LOCK_MINUTES = 15
MIN_PASSWORD_LEN = 8


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


class AuthService:
    def __init__(self, db: Database, audit: AuditService):
        self.db = db
        self.audit = audit

    def is_initialized(self) -> bool:
        return (self.db.scalar("SELECT COUNT(*) FROM users") or 0) > 0

    def setup_admin(self, username: str, full_name: str, password: str) -> SessionContext:
        """Create the first administrator. No hardcoded credentials."""
        if self.is_initialized():
            raise ValidationError("ইতিমধ্যে একজন প্রশাসনিক ব্যবহারকারী রয়েছে।")
        username = require_non_empty(username, "ব্যবহারকারীর নাম").lower()
        full_name = require_non_empty(full_name, "পূর্ণ নাম")
        self._validate_password(password)
        with self.db.transaction() as conn:
            cur = conn.execute(
                "INSERT INTO users (username, full_name, password_hash) VALUES (?,?,?)",
                (username, full_name, hash_password(password)),
            )
            user_id = cur.lastrowid
            owner_role = conn.execute("SELECT id FROM roles WHERE name='owner'").fetchone()["id"]
            conn.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (?,?)", (user_id, owner_role)
            )
        self.audit.log(None, "admin.setup", entity_type="user", entity_id=user_id)
        return self._build_context(user_id)

    def login(self, username: str, password: str) -> SessionContext:
        username = require_non_empty(username, "ব্যবহারকারীর নাম").lower()
        row = self.db.query_one("SELECT * FROM users WHERE username=?", (username,))
        if row is None:
            self.audit.log(None, "login.failed", details={"username": username})
            raise ValidationError("ব্যবহারকারীর নাম বা পাসওয়ার্ড সঠিক নয়।")
        if not row["is_active"]:
            raise ValidationError("এই ব্যবহারকারী নিষ্ক্রিয়।")
        locked_until = row["locked_until"]
        if locked_until:
            try:
                if datetime.fromisoformat(locked_until.replace("Z", "+00:00")) > _now():
                    raise ValidationError("অনেকবার ভুল চেষ্টায় হিসাবটি সাময়িকভাবে বন্ধ। পরে চেষ্টা করুন।")
            except ValueError:
                pass
        if not verify_password(row["password_hash"], password):
            self._register_failure(row["id"], row["failed_attempts"])
            self.audit.log(None, "login.failed", entity_type="user", entity_id=row["id"])
            raise ValidationError("ব্যবহারকারীর নাম বা পাসওয়ার্ড সঠিক নয়।")
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE users SET failed_attempts=0, locked_until=NULL WHERE id=?", (row["id"],)
            )
            if needs_rehash(row["password_hash"]):
                conn.execute(
                    "UPDATE users SET password_hash=? WHERE id=?",
                    (hash_password(password), row["id"]),
                )
        ctx = self._build_context(row["id"])
        self.audit.log(ctx, "login.success", entity_type="user", entity_id=row["id"])
        return ctx

    def logout(self, ctx: SessionContext) -> None:
        self.audit.log(ctx, "logout", entity_type="user", entity_id=ctx.user_id)

    def change_password(self, ctx: SessionContext, current: str, new: str) -> None:
        row = self.db.query_one("SELECT password_hash FROM users WHERE id=?", (ctx.user_id,))
        if row is None or not verify_password(row["password_hash"], current):
            raise ValidationError("বর্তমান পাসওয়ার্ড সঠিক নয়।")
        self._validate_password(new)
        self.db.execute(
            "UPDATE users SET password_hash=?, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?",
            (hash_password(new), ctx.user_id),
        )
        self.audit.log(ctx, "password.change", entity_type="user", entity_id=ctx.user_id)

    def _register_failure(self, user_id: int, current: int) -> None:
        attempts = current + 1
        locked = _iso(_now() + timedelta(minutes=LOCK_MINUTES)) if attempts >= MAX_FAILED else None
        self.db.execute(
            "UPDATE users SET failed_attempts=?, locked_until=? WHERE id=?",
            (attempts, locked, user_id),
        )

    def _validate_password(self, password: str) -> None:
        if not password or len(password) < MIN_PASSWORD_LEN:
            raise ValidationError(f"পাসওয়ার্ড কমপক্ষে {MIN_PASSWORD_LEN} অক্ষরের হতে হবে।")

    def _build_context(self, user_id: int) -> SessionContext:
        row = self.db.query_one("SELECT * FROM users WHERE id=?", (user_id,))
        perms = self.db.query(
            """SELECT DISTINCT p.code FROM user_roles ur
               JOIN role_permissions rp ON rp.role_id = ur.role_id
               JOIN permissions p ON p.id = rp.permission_id WHERE ur.user_id=?""",
            (user_id,),
        )
        return SessionContext(
            user_id=user_id,
            username=row["username"],
            full_name=row["full_name"],
            permissions=frozenset(r["code"] for r in perms),
            login_at=_iso(_now()),
        )
