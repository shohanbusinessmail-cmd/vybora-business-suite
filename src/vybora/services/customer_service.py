"""Customer management: CRUD, opening balance (via equity), search, derived dues."""

from __future__ import annotations

from vybora.core.errors import ConflictError, NotFoundError, ValidationError
from vybora.core.validation import require_non_empty, validate_mobile_bd
from vybora.data.db import Database
from vybora.data.sequences import next_document_number
from vybora.domain import posting
from vybora.domain.accounting import ACCOUNTS_RECEIVABLE
from vybora.security.permissions import require
from vybora.security.session import SessionContext
from vybora.services.accounting_service import AccountingService
from vybora.services.audit_service import AuditService


class CustomerService:
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
        notes: str = "",
        opening_balance: int = 0,
        date: str,
        code: str | None = None,
    ) -> int:
        require(ctx, "customers.manage")
        name = require_non_empty(name, "গ্রাহকের নাম")
        mobile = validate_mobile_bd(mobile)
        if opening_balance < 0:
            raise ValidationError("প্রারম্ভিক বাকি ঋণাত্মক হতে পারবে না।")
        with self.db.transaction() as conn:
            code = code or next_document_number(conn, "customer")
            if conn.execute("SELECT id FROM customers WHERE code=?", (code,)).fetchone():
                raise ConflictError("এই গ্রাহক কোড ইতিমধ্যে রয়েছে।")
            cur = conn.execute(
                "INSERT INTO customers (code, name, mobile, address, notes, opening_balance) "
                "VALUES (?,?,?,?,?,?)",
                (code, name, mobile, address, notes, opening_balance),
            )
            cid = cur.lastrowid
            if opening_balance > 0:
                lines = posting.opening_balance_posting(
                    kind="customer_receivable",
                    amount=opening_balance,
                    party_type="customer",
                    party_id=cid,
                )
                self.accounting.post_lines(
                    conn,
                    date=date,
                    source_type="customer_opening",
                    source_id=cid,
                    memo="প্রারম্ভিক বাকি",
                    lines=lines,
                    user_id=ctx.user_id,
                )
        self.audit.log(
            ctx, "customer.create", entity_type="customer", entity_id=cid, details={"name": name}
        )
        return cid

    def update(self, ctx: SessionContext, customer_id: int, **fields) -> None:
        require(ctx, "customers.manage")
        self.get(customer_id)
        allowed = {"name", "mobile", "address", "notes"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if "mobile" in updates:
            updates["mobile"] = validate_mobile_bd(updates["mobile"])
        if not updates:
            raise ValidationError("কোনো বৈধ ফিল্ড দেয়া হয়নি।")
        sets = ", ".join(f"{k}=?" for k in updates)
        self.db.execute(
            f"UPDATE customers SET {sets}, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?",
            (*updates.values(), customer_id),
        )
        self.audit.log(ctx, "customer.update", entity_type="customer", entity_id=customer_id)

    def get(self, customer_id: int) -> dict:
        row = self.db.query_one("SELECT * FROM customers WHERE id=?", (customer_id,))
        if row is None:
            raise NotFoundError("গ্রাহক পাওয়া যায়নি।")
        return dict(row)

    def set_active(self, ctx: SessionContext, customer_id: int, active: bool) -> None:
        require(ctx, "customers.manage")
        self.get(customer_id)
        self.db.execute(
            "UPDATE customers SET is_active=?, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?",
            (1 if active else 0, customer_id),
        )
        self.audit.log(ctx, "customer.active.change", entity_type="customer", entity_id=customer_id)

    def search(self, query: str = "", *, active_only: bool = True, limit: int = 100) -> list[dict]:
        sql = "SELECT * FROM customers WHERE 1=1"
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

    def balance(self, customer_id: int) -> int:
        """Outstanding receivable derived from AR subledger postings (debit - credit)."""
        return self.accounting.party_balance("customer", customer_id, ACCOUNTS_RECEIVABLE)

    def advance_balance(self, customer_id: int) -> int:
        row = self.db.query_one(
            "SELECT COALESCE(SUM(remaining),0) AS adv FROM customer_advances WHERE customer_id=?",
            (customer_id,),
        )
        return int(row["adv"]) if row else 0

    def ledger(
        self, customer_id: int, *, date_from: str | None = None, date_to: str | None = None
    ) -> list[dict]:
        sql = """SELECT je.date, je.entry_no, je.memo, je.source_type, jl.debit, jl.credit
                 FROM journal_lines jl JOIN journal_entries je ON je.id=jl.entry_id
                 WHERE jl.party_type='customer' AND jl.party_id=? AND jl.account_code=?"""
        params: list = [customer_id, ACCOUNTS_RECEIVABLE]
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
            running += int(r["debit"]) - int(r["credit"])
            out.append({**dict(r), "balance": running})
        return out
