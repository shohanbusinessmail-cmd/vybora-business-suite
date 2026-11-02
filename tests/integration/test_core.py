import pytest

from vybora.core.errors import ConflictError, NotFoundError, PermissionDeniedError, ValidationError
from vybora.domain.accounting import INVENTORY, OPENING_BALANCE_EQUITY
from vybora.services.container import build_services

DATE = "2026-11-02"


@pytest.fixture()
def env(db):
    svc = build_services(db)
    admin = svc.auth.setup_admin("admin", "মালিক", "strong-pass-123")
    return svc, admin


def _product(svc, ctx, **kw):
    defaults = dict(name="চাল", sku="RICE-1", unit_id=1, selling_price=8_000, purchase_price=5_000)
    defaults.update(kw)
    return svc.products.create(ctx, **defaults)


def test_product_create_and_search(env):
    svc, ctx = env
    pid = _product(svc, ctx)
    assert svc.products.get(pid)["name"] == "চাল"
    found = svc.products.search("চাল")
    assert any(p["id"] == pid for p in found)
    assert svc.products.lookup("RICE-1")["id"] == pid


def test_duplicate_sku_rejected(env):
    svc, ctx = env
    _product(svc, ctx)
    with pytest.raises(ConflictError):
        _product(svc, ctx, name="আরেকটি")


def test_barcode_lookup(env):
    svc, ctx = env
    pid = _product(svc, ctx, barcode="8901234567890")
    assert svc.products.lookup("8901234567890")["id"] == pid


def test_price_history_recorded(env):
    svc, ctx = env
    pid = _product(svc, ctx)
    svc.products.update(ctx, pid, selling_price=9_000)
    hist = svc.db.query(
        "SELECT * FROM product_price_history WHERE product_id=? AND field='selling_price'", (pid,)
    )
    assert len(hist) == 2  # initial + change
    assert hist[-1]["new_value"] == 9_000


def test_referenced_product_cannot_be_deleted(env):
    svc, ctx = env
    pid = _product(svc, ctx)
    svc.inventory.opening_stock(ctx, pid, 10_000, 5_000, date=DATE)
    with pytest.raises(ConflictError):
        svc.products.delete(ctx, pid)
    # Deactivation is allowed.
    svc.products.set_active(ctx, pid, False)
    assert svc.products.get(pid)["is_active"] == 0


def test_unreferenced_product_can_be_deleted(env):
    svc, ctx = env
    pid = _product(svc, ctx)
    svc.products.delete(ctx, pid)
    with pytest.raises(NotFoundError):
        svc.products.get(pid)


def test_opening_stock_posts_journal_and_pool(env):
    svc, ctx = env
    pid = _product(svc, ctx)
    svc.inventory.opening_stock(ctx, pid, 10_000, 5_000, date=DATE)
    p = svc.products.get(pid)
    assert p["stock_qty"] == 10_000 and p["stock_value"] == 50_000
    # Inventory GL == pool value; opening equity credited.
    assert svc.accounting.account_balance(INVENTORY) == 50_000
    assert svc.accounting.account_balance(OPENING_BALANCE_EQUITY) == -50_000
    d, c = svc.accounting.trial_balance_totals()
    assert d == c


def test_adjustment_up_and_down(env):
    svc, ctx = env
    pid = _product(svc, ctx)
    svc.inventory.opening_stock(ctx, pid, 10_000, 5_000, date=DATE)
    svc.inventory.adjust(ctx, pid, 2_000, date=DATE, reason="গণনা সংশোধন", reference_cost=5_000)
    assert svc.products.get(pid)["stock_qty"] == 12_000
    svc.inventory.adjust(ctx, pid, -3_000, date=DATE, reason="ক্ষতি", write_off=True)
    p = svc.products.get(pid)
    assert p["stock_qty"] == 9_000
    d, c = svc.accounting.trial_balance_totals()
    assert d == c


def test_adjustment_idempotent(env):
    svc, ctx = env
    pid = _product(svc, ctx)
    svc.inventory.opening_stock(ctx, pid, 10_000, 5_000, date=DATE)
    a1 = svc.inventory.adjust(
        ctx, pid, 1_000, date=DATE, reason="x", reference_cost=5_000, request_id="req-1"
    )
    a2 = svc.inventory.adjust(
        ctx, pid, 1_000, date=DATE, reason="x", reference_cost=5_000, request_id="req-1"
    )
    assert a1 == a2
    assert svc.products.get(pid)["stock_qty"] == 11_000  # applied once


def test_customer_opening_balance_via_equity(env):
    svc, ctx = env
    cid = svc.customers.create(ctx, name="রহিম", opening_balance=15_000, date=DATE)
    assert svc.customers.balance(cid) == 15_000
    # Not revenue: sales revenue account is zero.
    from vybora.domain.accounting import SALES_REVENUE

    assert svc.accounting.account_balance(SALES_REVENUE) == 0
    d, c = svc.accounting.trial_balance_totals()
    assert d == c


def test_supplier_opening_balance_via_equity(env):
    svc, ctx = env
    sid = svc.suppliers.create(ctx, name="করিম ট্রেডার্স", opening_balance=20_000, date=DATE)
    assert svc.suppliers.balance(sid) == 20_000
    d, c = svc.accounting.trial_balance_totals()
    assert d == c


def test_stock_valuation_matches_gl(env):
    svc, ctx = env
    p1 = _product(svc, ctx, sku="A")
    p2 = _product(svc, ctx, name="ডাল", sku="B")
    svc.inventory.opening_stock(ctx, p1, 10_000, 5_000, date=DATE)
    svc.inventory.opening_stock(ctx, p2, 5_000, 12_000, date=DATE)
    assert svc.inventory.valuation() == svc.accounting.account_balance(INVENTORY)


def test_low_stock_alerts(env):
    svc, ctx = env
    pid = _product(svc, ctx, min_stock_qty=5_000)
    svc.inventory.opening_stock(ctx, pid, 3_000, 5_000, date=DATE)
    low = svc.inventory.low_stock()
    assert any(p["id"] == pid for p in low)


def test_permission_required_for_product(env):
    svc, admin = env
    svc.users.create_user(admin, "cashier1", "ক্যাশিয়ার", "cashier-pass-123", "cashier")
    cashier = svc.auth.login("cashier1", "cashier-pass-123")
    with pytest.raises(PermissionDeniedError):
        _product(svc, cashier)


def test_invalid_mobile_rejected(env):
    svc, ctx = env
    with pytest.raises(ValidationError):
        svc.customers.create(ctx, name="x", mobile="12345", date=DATE)


def test_batch_and_expiry(env):
    svc, ctx = env
    pid = _product(svc, ctx)
    bid = svc.inventory.add_batch(ctx, pid, "B-001", expires_on="2026-11-10")
    assert bid > 0
    alerts = svc.inventory.expiry_alerts(within_days=30, today="2026-11-02")
    # batch qty is 0 so not alerted yet; just ensure query runs.
    assert isinstance(alerts, list)
