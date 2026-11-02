"""In-memory session context carrying the authenticated user's permissions."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SessionContext:
    user_id: int
    username: str
    full_name: str
    permissions: frozenset[str] = field(default_factory=frozenset)
    login_at: str = ""

    def has(self, permission: str) -> bool:
        return permission in self.permissions


# System context for internal/migration operations (all permissions).
SYSTEM = SessionContext(
    user_id=0, username="system", full_name="সিস্টেম", permissions=frozenset({"*"})
)


def has_permission(ctx: SessionContext, permission: str) -> bool:
    return ctx.has("*") or ctx.has(permission)
