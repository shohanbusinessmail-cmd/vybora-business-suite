import pytest

from vybora.core.errors import DatabaseError
from vybora.data.db import Database
from vybora.data.migrations import current_version, migrate


def test_migrations_apply(db):
    assert current_version(db) == 2
    # Seed data present
    assert db.scalar("SELECT COUNT(*) FROM accounts") >= 22
    assert db.scalar("SELECT COUNT(*) FROM units") == 10
    assert db.scalar("SELECT COUNT(*) FROM roles") == 5
    assert db.scalar("SELECT COUNT(*) FROM permissions") == 21
    assert db.scalar("SELECT COUNT(*) FROM payment_methods") == 4
    assert db.scalar("SELECT COUNT(*) FROM expense_categories") == 10


def test_pragmas(db):
    assert db.scalar("PRAGMA journal_mode").lower() == "wal"
    assert db.scalar("PRAGMA foreign_keys") == 1


def test_foreign_keys_enforced(db):
    with pytest.raises(DatabaseError):
        db.execute("INSERT INTO products (name, sku, unit_id) VALUES ('x','SKU1', 9999)")


def test_duplicate_sku_rejected(db):
    db.execute("INSERT INTO products (name, sku, unit_id) VALUES ('a','SKU1',1)")
    with pytest.raises(DatabaseError):
        db.execute("INSERT INTO products (name, sku, unit_id) VALUES ('b','SKU1',1)")


def test_duplicate_barcode_rejected(db):
    db.execute("INSERT INTO products (name, sku, unit_id) VALUES ('a','SKU1',1)")
    pid = db.scalar("SELECT id FROM products WHERE sku='SKU1'")
    db.execute("INSERT INTO barcodes (product_id, barcode) VALUES (?, '123')", (pid,))
    with pytest.raises(DatabaseError):
        db.execute("INSERT INTO barcodes (product_id, barcode) VALUES (?, '123')", (pid,))


def test_sale_paid_plus_due_check(db):
    with pytest.raises(DatabaseError):
        db.execute(
            """INSERT INTO sales (request_id, invoice_no, date, subtotal, total, paid, due)
               VALUES ('r1','INV-1','2026-11-02',100,100,60,50)"""
        )


def test_journal_line_xor_check(db):
    db.execute(
        "INSERT INTO journal_entries (entry_no, date, source_type) VALUES ('J1','2026-11-02','test')"
    )
    eid = db.scalar("SELECT id FROM journal_entries WHERE entry_no='J1'")
    with pytest.raises(DatabaseError):
        db.execute(
            "INSERT INTO journal_lines (entry_id, account_code, debit, credit) VALUES (?, '1000', 5, 5)",
            (eid,),
        )


def test_transaction_atomicity(db):
    try:
        with db.transaction() as conn:
            conn.execute("INSERT INTO categories (name) VALUES ('cat1')")
            raise RuntimeError("force rollback")
    except RuntimeError:
        pass
    assert db.scalar("SELECT COUNT(*) FROM categories WHERE name='cat1'") == 0


def test_transaction_commit(db):
    with db.transaction() as conn:
        conn.execute("INSERT INTO categories (name) VALUES ('cat2')")
    assert db.scalar("SELECT COUNT(*) FROM categories WHERE name='cat2'") == 1


def test_idempotency_unique_request_id(db):
    db.execute("""INSERT INTO sales (request_id, invoice_no, date, subtotal, total, paid, due)
                  VALUES ('dup','INV-1','2026-11-02',100,100,100,0)""")
    with pytest.raises(DatabaseError):
        db.execute("""INSERT INTO sales (request_id, invoice_no, date, subtotal, total, paid, due)
                      VALUES ('dup','INV-2','2026-11-02',100,100,100,0)""")


def test_migration_checksum_tamper(tmp_path):

    database = Database(tmp_path / "t.db")
    migrate(database)
    # Tamper with an applied migration file's recorded checksum.
    database.execute("UPDATE schema_migrations SET checksum='tampered' WHERE version=1")
    with pytest.raises(DatabaseError):
        migrate(database)
    database.close()


def test_migration_idempotent(db):
    v1 = current_version(db)
    migrate(db)
    assert current_version(db) == v1


def test_owner_role_has_all_permissions(db):
    owner_perms = db.scalar(
        """SELECT COUNT(*) FROM role_permissions rp
           JOIN roles r ON r.id=rp.role_id WHERE r.name='owner'"""
    )
    total = db.scalar("SELECT COUNT(*) FROM permissions")
    assert owner_perms == total


def test_cashier_cannot_manage_users(db):
    rows = db.query(
        """SELECT p.code FROM role_permissions rp
           JOIN roles r ON r.id=rp.role_id JOIN permissions p ON p.id=rp.permission_id
           WHERE r.name='cashier'"""
    )
    codes = {r["code"] for r in rows}
    assert "users.manage" not in codes
    assert "sales.create" in codes
