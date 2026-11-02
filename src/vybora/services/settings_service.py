"""Business information and application settings."""

from __future__ import annotations

from vybora.core.errors import ValidationError
from vybora.core.formatting import DisplayPrefs
from vybora.data.db import Database
from vybora.security.permissions import require
from vybora.security.session import SessionContext
from vybora.services.audit_service import AuditService

_INT_KEYS = {"decimal_places", "tax_rate_bp", "backup_retention", "idle_lock_minutes"}
_BOOL_KEYS = {"thousand_separator", "currency_prefix", "tax_recoverable", "allow_negative_stock"}


class SettingsService:
    def __init__(self, db: Database, audit: AuditService):
        self.db = db
        self.audit = audit

    def get(self, key: str, default: str = "") -> str:
        row = self.db.query_one("SELECT value FROM business_settings WHERE key=?", (key,))
        return row["value"] if row else default

    def get_int(self, key: str, default: int = 0) -> int:
        try:
            return int(self.get(key, str(default)))
        except ValueError:
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        return self.get(key, "1" if default else "0") == "1"

    def set(self, ctx: SessionContext, key: str, value: str) -> None:
        require(ctx, "settings.manage")
        if key in _INT_KEYS:
            try:
                int(value)
            except ValueError as exc:
                raise ValidationError("সংখ্যাসূচক সেটিং মান অবৈধ।") from exc
        if key in _BOOL_KEYS and value not in ("0", "1"):
            raise ValidationError("বুলিয়ান সেটিং মান অবৈধ।")
        if key == "tax_mode" and value not in ("none", "exclusive", "inclusive"):
            raise ValidationError("কর মোড অবৈধ।")
        self.db.execute(
            "INSERT INTO business_settings (key, value) VALUES (?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        self.audit.log(ctx, "settings.change", details={"key": key})

    def display_prefs(self) -> DisplayPrefs:
        return DisplayPrefs(
            bengali_digits=self.get("digit_mode", "bengali") == "bengali",
            thousand_separator=self.get_bool("thousand_separator", True),
            decimal_places=self.get_int("decimal_places", 2),
            currency_prefix=self.get_bool("currency_prefix", True),
            date_format=self.get("date_format", "dd/mm/yyyy"),
        )

    def business(self) -> dict:
        row = self.db.query_one("SELECT * FROM businesses WHERE id=1")
        return dict(row) if row else {}

    def update_business(self, ctx: SessionContext, **fields) -> None:
        require(ctx, "settings.manage")
        allowed = {
            "name",
            "owner_name",
            "address",
            "phone",
            "email",
            "logo_path",
            "business_type",
            "invoice_footer",
            "currency",
        }
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            raise ValidationError("কোনো বৈধ ফিল্ড দেয়া হয়নি।")
        sets = ", ".join(f"{k}=?" for k in updates)
        self.db.execute(
            f"UPDATE businesses SET {sets}, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=1",
            tuple(updates.values()),
        )
        self.audit.log(ctx, "business.update", details={"fields": list(updates)})

    def tax_mode(self) -> str:
        return self.get("tax_mode", "none")

    def tax_rate_bp(self) -> int:
        return self.get_int("tax_rate_bp", 0)

    def allow_negative_stock(self) -> bool:
        return self.get_bool("allow_negative_stock", False)
