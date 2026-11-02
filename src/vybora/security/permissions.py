"""Permission enforcement helpers. Service-layer checks are authoritative."""

from __future__ import annotations

from vybora.core.errors import PermissionDeniedError
from vybora.security.session import SessionContext, has_permission

# Canonical permission codes (seeded in migration 0001).
ALL_PERMISSIONS = [
    "sales.view",
    "sales.create",
    "sales.cancel",
    "sales.return",
    "costs.view",
    "profits.view",
    "products.manage",
    "stock.manage",
    "stock.adjust",
    "customers.manage",
    "suppliers.manage",
    "payments.record",
    "purchases.manage",
    "expenses.manage",
    "reports.view",
    "users.manage",
    "backup.manage",
    "backup.restore",
    "settings.manage",
    "audit.view",
    "license.manage",
]


def require(ctx: SessionContext, permission: str) -> None:
    if not has_permission(ctx, permission):
        raise PermissionDeniedError()
