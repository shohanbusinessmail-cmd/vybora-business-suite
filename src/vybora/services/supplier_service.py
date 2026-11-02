"""Supplier management: CRUD, opening balance (via equity), search, derived payables."""

from __future__ import annotations

from vybora.core.errors import ConflictError, NotFoundError, ValidationError
from vybora.core.validation import require_non_empty, validate_mobile_bd
from vybora.data.db import Database
from vybora.data.sequences import next_document_number
from vybora.domain import posting
from vybora.domain.accounting import ACCOUNTS_PAYABLE
from vybora.security.permissions import require
from vybora.security.session import SessionContext
from vybora.services.accounting_service import AccountingService
from vybora.services.audit_service import AuditService


class SupplierService:
    def __init__(self, db: Database, audit: AuditService, accounting: AccountingService):
        self.db = db
        self.audit = audit
        self.accounting = accounting

    def create(
        self,
        ctx: SessionContext,
        *,
        name: str,
        mobile: str | None = None,
        address: str = "",
        business_info: str = "",
        notes: str = "",
        opening_balance: int = 0,
        date: str,
        code: str | None = None,
    ) -> int:
        require(ctx, "suppliers.manage")
        name = require_non_empty(name, "সরবরাহকারীর নাম")
        mobile = validate_mobile_bd(mobile)
        if opening_balance < 0:
            raise ValidationError("প্রারম্ভিক প্রদেয় ঋণাত্মক হতে পারবে না।")
        with self.db.transaction() as conn:
            code = code or next_document_number(conn, "supplier")
            if conn.execute("SELECT id FROM suppliers WHERE code=?", (code,)).fetchone():
                raise ConflictError("এই সরবরাহকারী কোড ইতিমধ্যে রয়েছে।")
            cur = conn.execute(
                "INSERT INTO suppliers (code, name, mobile, address, business_info, notes, opening_balance) "
                "VALUES (?,?,?,?,?,?,?)",
                (code, name, mobile, address, business_info, notes, opening_balance),
            )
            sid = cur.lastrowid
            if opening_balance > 0:
                lines = posting.opening_balance_posting(
                    kind="supplier_payable",
                    amount=opening_balance,
                    party_type="supplier",
                    party_id=sid,
                )
                self.accounting.post_lines(
                    conn,
                    date=date,
                    source_type="supplier_opening",
                    source_id=sid,
                    memo="প্রারম্ভিক প্রদেয়",
                    lines=lines,
                    user_id=ctx.user_id,
                )
        self.audit.log(
            ctx, "supplier.create", entity_type="supplier", entity_id=sid, details={"name": name}
        )
        return sid

    def update(self, ctx: SessionContext, supplier_id: int, **fields) -> None:
        require(ctx, "suppliers.manage")
        self.get(supplier_id)
        allowed = {"name", "mobile", "address", "business_info", "notes"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if "mobile" in updates:
            updates["mobile"] = validate_mobile_bd(updates["mobile"])
        if not updates:
            raise ValidationError("কোনো বৈধ ফিল্ড দেয়া হয়নি।")
        sets = ", ".join(f"{k}=?" for k in updates)
        self.db.execute(
            f"UPDATE suppliers SET {sets}, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?",
            (*updates.values(), supplier_id),
        )
        self.audit.log(ctx, "supplier.update", entity_type="supplier", entity_id=supplier_id)

    def get(self, supplier_id: int) -> dict:
        row = self.db.query_one("SELECT * FROM suppliers WHERE id=?", (supplier_id,))
        if row is None:
            raise NotFoundError("সরবরাহকারী পাওয়া যায়নি।")
        return dict(row)

    def set_active(self, ctx: SessionContext, supplier_id: int, active: bool) -> None:
        require(ctx, "suppliers.manage")
        self.get(supplier_id)
        self.db.execute(
            "UPDATE suppliers SET is_active=?, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?",
            (1 if active else 0, supplier_id),
        )
        self.audit.log(ctx, "supplier.active.change", entity_type="supplier", entity_id=supplier_id)

    def search(self, query: str = "", *, active_only: bool = True, limit: int = 100) -> list[dict]:
        sql = "SELECT * FROM suppliers WHERE 1=1"
        params: list = []
        if query:
            sql += " AND (name LIKE ? OR mobile LIKE ? OR code LIKE ?)"
            like = f"%{query}%"
            params += [like, like, like]
        if active_only:
            sql += " AND is_active=1"
        sql += " ORDER BY name LIMIT ?"
        params.append(limit)
        return [dict(r) for r in self.db.query(sql, tuple(params))]

    def balance(self, supplier_id: int) -> int:
        """Outstanding payable derived from AP subledger (credit - debit)."""
        return -self.accounting.party_balance("supplier", supplier_id, ACCOUNTS_PAYABLE)

    def ledger(
        self, supplier_id: int, *, date_from: str | None = None, date_to: str | None = None
    ) -> list[dict]:
        sql = """SELECT je.date, je.entry_no, je.memo, je.source_type, jl.debit, jl.credit
                 FROM journal_lines jl JOIN journal_entries je ON je.id=jl.entry_id
                 WHERE jl.party_type='supplier' AND jl.party_id=? AND jl.account_code=?"""
        params: list = [supplier_id, ACCOUNTS_PAYABLE]
        if date_from:
            sql += " AND je.date>=?"
            params.append(date_from)
        if date_to:
            sql += " AND je.date<=?"
            params.append(date_to)
        sql += " ORDER BY je.date, je.id"
        running = 0
        out = []
        for r in self.db.query(sql, tuple(params)):
            running += int(r["credit"]) - int(r["debit"])
            out.append({**dict(r), "balance": running})
        return out
