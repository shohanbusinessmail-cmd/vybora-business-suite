"""Product management: CRUD, search, price history, barcodes, safe deactivation."""

from __future__ import annotations

from vybora.core.errors import ConflictError, NotFoundError, ValidationError
from vybora.core.validation import require_non_empty
from vybora.data.db import Database
from vybora.security.permissions import require
from vybora.security.session import SessionContext
from vybora.services.audit_service import AuditService

_PRICE_FIELDS = {"purchase_price", "selling_price", "wholesale_price"}


class ProductService:
    def __init__(self, db: Database, audit: AuditService):
        self.db = db
        self.audit = audit

    def create(
        self,
        ctx: SessionContext,
        *,
        name: str,
        sku: str,
        unit_id: int,
        category_id: int | None = None,
        brand_id: int | None = None,
        purchase_price: int = 0,
        selling_price: int = 0,
        wholesale_price: int = 0,
        min_stock_qty: int = 0,
        description: str = "",
        barcode: str | None = None,
    ) -> int:
        require(ctx, "products.manage")
        name = require_non_empty(name, "পণ্যের নাম")
        sku = require_non_empty(sku, "SKU")
        if self.db.query_one("SELECT id FROM products WHERE sku=?", (sku,)):
            raise ConflictError("এই SKU ইতিমধ্যে রয়েছে।")
        if not self.db.query_one("SELECT id FROM units WHERE id=?", (unit_id,)):
            raise ValidationError("একক পাওয়া যায়নি।")
        for v in (purchase_price, selling_price, wholesale_price, min_stock_qty):
            if v < 0:
                raise ValidationError("মূল্য ও মজুত ঋণাত্মক হতে পারবে না।")
        if barcode and self.db.query_one("SELECT id FROM barcodes WHERE barcode=?", (barcode,)):
            raise ConflictError("এই বারকোড ইতিমধ্যে রয়েছে।")
        with self.db.transaction() as conn:
            cur = conn.execute(
                """INSERT INTO products (name, sku, category_id, brand_id, unit_id,
                       purchase_price, selling_price, wholesale_price, min_stock_qty, description)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    name,
                    sku,
                    category_id,
                    brand_id,
                    unit_id,
                    purchase_price,
                    selling_price,
                    wholesale_price,
                    min_stock_qty,
                    description,
                ),
            )
            pid = cur.lastrowid
            if barcode:
                conn.execute(
                    "INSERT INTO barcodes (product_id, barcode) VALUES (?,?)", (pid, barcode)
                )
            for field, val in (
                ("purchase_price", purchase_price),
                ("selling_price", selling_price),
                ("wholesale_price", wholesale_price),
            ):
                conn.execute(
                    "INSERT INTO product_price_history (product_id, field, old_value, new_value, user_id) "
                    "VALUES (?,?,0,?,?)",
                    (pid, field, val, ctx.user_id),
                )
        self.audit.log(
            ctx,
            "product.create",
            entity_type="product",
            entity_id=pid,
            details={"name": name, "sku": sku},
        )
        return pid

    def update(self, ctx: SessionContext, product_id: int, **fields) -> None:
        require(ctx, "products.manage")
        product = self.get(product_id)
        allowed = {
            "name",
            "category_id",
            "brand_id",
            "unit_id",
            "purchase_price",
            "selling_price",
            "wholesale_price",
            "min_stock_qty",
            "description",
            "image_path",
        }
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            raise ValidationError("কোনো বৈধ ফিল্ড দেয়া হয়নি।")
        for k in _PRICE_FIELDS & updates.keys():
            if updates[k] < 0:
                raise ValidationError("মূল্য ঋণাত্মক হতে পারবে না।")
        with self.db.transaction() as conn:
            for k in _PRICE_FIELDS & updates.keys():
                if updates[k] != product[k]:
                    conn.execute(
                        "INSERT INTO product_price_history (product_id, field, old_value, new_value, user_id) "
                        "VALUES (?,?,?,?,?)",
                        (product_id, k, product[k], updates[k], ctx.user_id),
                    )
                    self.audit.log(
                        ctx,
                        "price.change",
                        entity_type="product",
                        entity_id=product_id,
                        details={"field": k, "old": product[k], "new": updates[k]},
                    )
            sets = ", ".join(f"{k}=?" for k in updates)
            conn.execute(
                f"UPDATE products SET {sets}, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?",
                (*updates.values(), product_id),
            )
        self.audit.log(ctx, "product.update", entity_type="product", entity_id=product_id)

    def get(self, product_id: int) -> dict:
        row = self.db.query_one("SELECT * FROM products WHERE id=?", (product_id,))
        if row is None:
            raise NotFoundError("পণ্য পাওয়া যায়নি।")
        return dict(row)

    def set_active(self, ctx: SessionContext, product_id: int, active: bool) -> None:
        require(ctx, "products.manage")
        self.get(product_id)
        self.db.execute(
            "UPDATE products SET is_active=?, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?",
            (1 if active else 0, product_id),
        )
        self.audit.log(
            ctx,
            "product.deactivate" if not active else "product.activate",
            entity_type="product",
            entity_id=product_id,
        )

    def delete(self, ctx: SessionContext, product_id: int) -> None:
        """Hard-delete only if never referenced by any transaction; else deactivation required."""
        require(ctx, "products.manage")
        self.get(product_id)
        referenced = self.db.scalar(
            """SELECT (SELECT COUNT(*) FROM sale_items WHERE product_id=?)
                   + (SELECT COUNT(*) FROM purchase_items WHERE product_id=?)
                   + (SELECT COUNT(*) FROM stock_movements WHERE product_id=?)""",
            (product_id, product_id, product_id),
        )
        if referenced:
            raise ConflictError("এই পণ্যটি লেনদেনে ব্যবহৃত হয়েছে। মুছে ফেলা যায় না; নিষ্ক্রিয় করুন।")
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM barcodes WHERE product_id=?", (product_id,))
            conn.execute("DELETE FROM product_price_history WHERE product_id=?", (product_id,))
            conn.execute("DELETE FROM products WHERE id=?", (product_id,))
        self.audit.log(ctx, "product.delete", entity_type="product", entity_id=product_id)

    def search(
        self,
        query: str = "",
        *,
        category_id: int | None = None,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        sql = """SELECT p.*, c.name AS category_name, u.name AS unit_name, u.allows_fraction
                 FROM products p
                 LEFT JOIN categories c ON c.id=p.category_id
                 LEFT JOIN units u ON u.id=p.unit_id WHERE 1=1"""
        params: list = []
        if query:
            sql += " AND (p.name LIKE ? OR p.sku LIKE ? OR p.id IN (SELECT product_id FROM barcodes WHERE barcode LIKE ?))"
            like = f"%{query}%"
            params += [like, like, like]
        if category_id is not None:
            sql += " AND p.category_id=?"
            params.append(category_id)
        if active_only:
            sql += " AND p.is_active=1"
        sql += " ORDER BY p.name LIMIT ? OFFSET ?"
        params += [limit, offset]
        return [dict(r) for r in self.db.query(sql, tuple(params))]

    def lookup(self, code: str) -> dict | None:
        """Exact lookup by barcode, SKU, then name (for scanners)."""
        row = self.db.query_one(
            """SELECT p.* FROM products p JOIN barcodes b ON b.product_id=p.id
               WHERE b.barcode=? AND p.is_active=1""",
            (code,),
        )
        if row is None:
            row = self.db.query_one("SELECT * FROM products WHERE sku=? AND is_active=1", (code,))
        if row is None:
            row = self.db.query_one("SELECT * FROM products WHERE name=? AND is_active=1", (code,))
        return dict(row) if row else None

    def bulk_price_update(
        self, ctx: SessionContext, product_ids: list[int], *, field: str, percent_bp: int
    ) -> int:
        """Adjust a price field by a percentage (basis points). Returns count updated."""
        require(ctx, "products.manage")
        if field not in _PRICE_FIELDS:
            raise ValidationError("মূল্য ফিল্ড অবৈধ।")
        from vybora.core.money import round_half_up

        count = 0
        with self.db.transaction() as conn:
            for pid in product_ids:
                row = conn.execute(f"SELECT {field} FROM products WHERE id=?", (pid,)).fetchone()
                if row is None:
                    continue
                old = row[field]
                new = max(0, round_half_up(old * (10000 + percent_bp), 10000))
                conn.execute(
                    f"UPDATE products SET {field}=?, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?",
                    (new, pid),
                )
                conn.execute(
                    "INSERT INTO product_price_history (product_id, field, old_value, new_value, user_id) "
                    "VALUES (?,?,?,?,?)",
                    (pid, field, old, new, ctx.user_id),
                )
                count += 1
        self.audit.log(
            ctx,
            "product.bulk_price",
            details={"field": field, "percent_bp": percent_bp, "count": count},
        )
        return count
