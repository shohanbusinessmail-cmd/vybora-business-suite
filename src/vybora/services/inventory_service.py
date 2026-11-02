"""Inventory: opening stock, adjustments, write-offs, movements, valuation.

The stock pool (products.stock_qty/stock_value/last_avg_cost) is authoritative.
Every change writes an auditable stock_movements row; financial changes post journals.
"""

from __future__ import annotations

import sqlite3
import uuid

from vybora.core.errors import NotFoundError, ValidationError
from vybora.data.db import Database
from vybora.domain import posting
from vybora.domain.inventory import StockPool, apply_adjustment
from vybora.security.permissions import require
from vybora.security.session import SessionContext
from vybora.services.accounting_service import AccountingService
from vybora.services.audit_service import AuditService


class InventoryService:
    def __init__(self, db: Database, audit: AuditService, accounting: AccountingService):
        self.db = db
        self.audit = audit
        self.accounting = accounting

    def _pool(self, conn: sqlite3.Connection, product_id: int) -> StockPool:
        row = conn.execute(
            "SELECT stock_qty, stock_value, last_avg_cost FROM products WHERE id=?", (product_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError("পণ্য পাওয়া যায়নি।")
        return StockPool(
            qty=row["stock_qty"], value=row["stock_value"], last_avg_cost=row["last_avg_cost"]
        )

    def _save_pool(self, conn: sqlite3.Connection, product_id: int, pool: StockPool) -> None:
        conn.execute(
            "UPDATE products SET stock_qty=?, stock_value=?, last_avg_cost=? WHERE id=?",
            (pool.qty, pool.value, pool.last_avg_cost, product_id),
        )

    def record_movement(
        self,
        conn: sqlite3.Connection,
        *,
        product_id: int,
        qty_delta: int,
        value_delta: int,
        reason: str,
        source_type: str,
        source_id: int | None,
        user_id: int | None,
        note: str = "",
        batch_id: int | None = None,
    ) -> None:
        """Insert an auditable stock movement row (does not change the pool)."""
        conn.execute(
            """INSERT INTO stock_movements (product_id, batch_id, qty_delta, value_delta, reason,
                   source_type, source_id, user_id, note) VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                product_id,
                batch_id,
                qty_delta,
                value_delta,
                reason,
                source_type,
                source_id,
                user_id,
                note,
            ),
        )

    def apply_stock_change(
        self,
        conn: sqlite3.Connection,
        *,
        product_id: int,
        qty_delta: int,
        value_delta: int,
        reason: str,
        source_type: str,
        source_id: int | None,
        user_id: int | None,
        note: str = "",
        batch_id: int | None = None,
    ) -> None:
        """Update the pool by explicit deltas and record a movement (caller computes deltas)."""
        from vybora.core.money import round_half_up

        row = conn.execute(
            "SELECT stock_qty, stock_value, last_avg_cost FROM products WHERE id=?", (product_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError("পণ্য পাওয়া যায়নি।")
        new_qty = row["stock_qty"] + qty_delta
        new_value = row["stock_value"] + value_delta
        new_avg = round_half_up(new_value * 1000, new_qty) if new_qty > 0 else row["last_avg_cost"]
        conn.execute(
            "UPDATE products SET stock_qty=?, stock_value=?, last_avg_cost=? WHERE id=?",
            (new_qty, new_value, new_avg, product_id),
        )
        self.record_movement(
            conn,
            product_id=product_id,
            qty_delta=qty_delta,
            value_delta=value_delta,
            reason=reason,
            source_type=source_type,
            source_id=source_id,
            user_id=user_id,
            note=note,
            batch_id=batch_id,
        )

    def opening_stock(
        self,
        ctx: SessionContext,
        product_id: int,
        qty: int,
        unit_cost: int,
        *,
        date: str,
        note: str = "",
    ) -> int:
        require(ctx, "stock.manage")
        if qty <= 0 or unit_cost < 0:
            raise ValidationError("পরিমাণ ধনাত্মক এবং মূল্য অঋণাত্মক হতে হবে।")
        from vybora.core.money import round_half_up

        value = round_half_up(qty * unit_cost, 1000)
        request_id = uuid.uuid4().hex
        with self.db.transaction() as conn:
            self.apply_stock_change(
                conn,
                product_id=product_id,
                qty_delta=qty,
                value_delta=value,
                reason="opening",
                source_type="opening",
                source_id=None,
                user_id=ctx.user_id,
                note=note,
            )
            lines = posting.opening_balance_posting(kind="inventory", amount=value)
            journal_id = self.accounting.post_lines(
                conn,
                date=date,
                source_type="opening",
                source_id=product_id,
                memo="প্রারম্ভিক মজুত",
                lines=lines,
                user_id=ctx.user_id,
            )
            conn.execute(
                "UPDATE stock_adjustments SET journal_id=? WHERE request_id=?",
                (journal_id, request_id),
            )
        self.audit.log(
            ctx,
            "stock.opening",
            entity_type="product",
            entity_id=product_id,
            details={"qty": qty, "value": value},
        )
        return journal_id

    def adjust(
        self,
        ctx: SessionContext,
        product_id: int,
        qty_delta: int,
        *,
        date: str,
        reason: str,
        note: str = "",
        reference_cost: int = 0,
        write_off: bool = False,
        request_id: str | None = None,
    ) -> int:
        require(ctx, "stock.adjust")
        if qty_delta == 0:
            raise ValidationError("সমন্বয়ের পরিমাণ শূন্য হতে পারবে না।")
        if not reason.strip():
            raise ValidationError("সমন্বয়ের কারণ আবশ্যক।")
        request_id = request_id or uuid.uuid4().hex
        existing = self.db.query_one(
            "SELECT id FROM stock_adjustments WHERE request_id=?", (request_id,)
        )
        if existing:
            return existing["id"]  # idempotent
        with self.db.transaction() as conn:
            pool = self._pool(conn, product_id)
            value_delta, pool = apply_adjustment(pool, qty_delta, reference_cost)
            self._save_pool(conn, product_id, pool)
            self.record_movement(
                conn,
                product_id=product_id,
                qty_delta=qty_delta,
                value_delta=value_delta,
                reason="write_off" if write_off else "adjustment",
                source_type="adjustment",
                source_id=None,
                user_id=ctx.user_id,
                note=note,
            )
            lines = posting.adjustment_posting(value_delta=value_delta, write_off=write_off)
            journal_id = self.accounting.post_lines(
                conn,
                date=date,
                source_type="adjustment",
                source_id=product_id,
                memo=reason,
                lines=lines,
                user_id=ctx.user_id,
            )
            cur = conn.execute(
                """INSERT INTO stock_adjustments (request_id, product_id, qty_delta, value_delta,
                       reason, note, user_id, journal_id) VALUES (?,?,?,?,?,?,?,?)""",
                (
                    request_id,
                    product_id,
                    qty_delta,
                    value_delta,
                    reason,
                    note,
                    ctx.user_id,
                    journal_id,
                ),
            )
            adj_id = cur.lastrowid
        self.audit.log(
            ctx,
            "stock.adjust",
            entity_type="product",
            entity_id=product_id,
            details={"qty_delta": qty_delta, "value_delta": value_delta, "reason": reason},
        )
        return adj_id

    def movements(self, product_id: int, *, limit: int = 200) -> list[dict]:
        return [
            dict(r)
            for r in self.db.query(
                "SELECT * FROM stock_movements WHERE product_id=? ORDER BY id DESC LIMIT ?",
                (product_id, limit),
            )
        ]

    def low_stock(self) -> list[dict]:
        return [
            dict(r)
            for r in self.db.query(
                """SELECT p.* FROM products p WHERE p.is_active=1 AND p.stock_qty <= p.min_stock_qty
               ORDER BY (p.stock_qty - p.min_stock_qty) ASC"""
            )
        ]

    def valuation(self) -> int:
        return int(
            self.db.scalar("SELECT COALESCE(SUM(stock_value),0) FROM products WHERE is_active=1")
            or 0
        )

    def add_batch(
        self,
        ctx: SessionContext,
        product_id: int,
        batch_no: str,
        *,
        expires_on: str | None = None,
        manufactured_on: str | None = None,
    ) -> int:
        require(ctx, "stock.manage")
        from vybora.core.validation import require_non_empty

        batch_no = require_non_empty(batch_no, "ব্যাচ নম্বর")
        with self.db.transaction() as conn:
            cur = conn.execute(
                "INSERT INTO batches (product_id, batch_no, manufactured_on, expires_on) VALUES (?,?,?,?)",
                (product_id, batch_no, manufactured_on, expires_on),
            )
            return cur.lastrowid

    def expiry_alerts(self, *, within_days: int = 30, today: str) -> list[dict]:
        return [
            dict(r)
            for r in self.db.query(
                """SELECT b.*, p.name AS product_name FROM batches b JOIN products p ON p.id=b.product_id
               WHERE b.expires_on IS NOT NULL AND b.qty>0 AND b.expires_on <= date(?, '+'||?||' days')
               ORDER BY b.expires_on""",
                (today, within_days),
            )
        ]
