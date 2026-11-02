"""User and role management (requires users.manage)."""

from __future__ import annotations

from vybora.core.errors import NotFoundError, ValidationError
from vybora.core.validation import require_non_empty
from vybora.data.db import Database
from vybora.security.passwords import hash_password
from vybora.security.permissions import require
from vybora.security.session import SessionContext
from vybora.services.audit_service import AuditService

VALID_ROLES = {"owner", "manager", "cashier", "inventory", "accountant"}


class UserService:
    def __init__(self, db: Database, audit: AuditService):
        self.db = db
        self.audit = audit

    def list_users(self, ctx: SessionContext) -> list[dict]:
        require(ctx, "users.manage")
        rows = self.db.query(
            """SELECT u.id, u.username, u.full_name, u.is_active, u.created_at,
                      GROUP_CONCAT(r.name) AS roles
               FROM users u
               LEFT JOIN user_roles ur ON ur.user_id = u.id
               LEFT JOIN roles r ON r.id = ur.role_id
               GROUP BY u.id ORDER BY u.id"""
        )
        return [dict(r) for r in rows]

    def create_user(
        self, ctx: SessionContext, username: str, full_name: str, password: str, role: str
    ) -> int:
        require(ctx, "users.manage")
        username = require_non_empty(username, "ব্যবহারকারীর নাম").lower()
        full_name = require_non_empty(full_name, "পূর্ণ নাম")
        if role not in VALID_ROLES:
            raise ValidationError("ভূমিকা অবৈধ।")
        if not password or len(password) < 8:
            raise ValidationError("পাসওয়ার্ড কমপক্ষে ৮ অক্ষরের হতে হবে।")
        if self.db.query_one("SELECT id FROM users WHERE username=?", (username,)):
            raise ValidationError("এই ব্যবহারকারীর নাম ইতিমধ্যে রয়েছে।")
        with self.db.transaction() as conn:
            cur = conn.execute(
                "INSERT INTO users (username, full_name, password_hash) VALUES (?,?,?)",
                (username, full_name, hash_password(password)),
            )
            user_id = cur.lastrowid
            role_id = conn.execute("SELECT id FROM roles WHERE name=?", (role,)).fetchone()["id"]
            conn.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (?,?)", (user_id, role_id)
            )
        self.audit.log(
            ctx,
            "user.create",
            entity_type="user",
            entity_id=user_id,
            details={"username": username, "role": role},
        )
        return user_id

    def set_role(self, ctx: SessionContext, user_id: int, role: str) -> None:
        require(ctx, "users.manage")
        if role not in VALID_ROLES:
            raise ValidationError("ভূমিকা অবৈধ।")
        if not self.db.query_one("SELECT id FROM users WHERE id=?", (user_id,)):
            raise NotFoundError("ব্যবহারকারী পাওয়া যায়নি।")
        with self.db.transaction() as conn:
            role_id = conn.execute("SELECT id FROM roles WHERE name=?", (role,)).fetchone()["id"]
            conn.execute("DELETE FROM user_roles WHERE user_id=?", (user_id,))
            conn.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (?,?)", (user_id, role_id)
            )
        self.audit.log(
            ctx, "user.role.change", entity_type="user", entity_id=user_id, details={"role": role}
        )

    def set_active(self, ctx: SessionContext, user_id: int, active: bool) -> None:
        require(ctx, "users.manage")
        if user_id == ctx.user_id and not active:
            raise ValidationError("নিজেকে নিষ্ক্রিয় করা যায় না।")
        if not self.db.query_one("SELECT id FROM users WHERE id=?", (user_id,)):
            raise NotFoundError("ব্যবহারকারী পাওয়া যায়নি।")
        self.db.execute(
            "UPDATE users SET is_active=?, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?",
            (1 if active else 0, user_id),
        )
        self.audit.log(
            ctx,
            "user.active.change",
            entity_type="user",
            entity_id=user_id,
            details={"active": active},
        )

    def reset_password(self, ctx: SessionContext, user_id: int, new_password: str) -> None:
        require(ctx, "users.manage")
        if not new_password or len(new_password) < 8:
            raise ValidationError("পাসওয়ার্ড কমপক্ষে ৮ অক্ষরের হতে হবে।")
        if not self.db.query_one("SELECT id FROM users WHERE id=?", (user_id,)):
            raise NotFoundError("ব্যবহারকারী পাওয়া যায়নি।")
        self.db.execute(
            "UPDATE users SET password_hash=?, failed_attempts=0, locked_until=NULL WHERE id=?",
            (hash_password(new_password), user_id),
        )
        self.audit.log(ctx, "user.password.reset", entity_type="user", entity_id=user_id)
