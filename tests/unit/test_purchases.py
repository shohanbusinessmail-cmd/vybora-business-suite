import pytest

from vybora.core.errors import ValidationError
from vybora.domain.purchases import PurchaseLine, compute_purchase
from vybora.domain.sales import TaxMode


def test_simple_purchase():
    lines = [PurchaseLine(1, 10_000, 5_000)]  # 10 @ 50
    t = compute_purchase(lines, 0, TaxMode.NONE)
    assert t.subtotal == 50_000 and t.total == 50_000 and t.inventory_value == 50_000


def test_additional_cost_allocation():
    lines = [PurchaseLine(1, 10_000, 5_000), PurchaseLine(2, 5_000, 10_000)]
    t = compute_purchase(lines, 3_000, TaxMode.NONE)  # 30.00 extra allocated
    assert sum(ln.additional_cost_share for ln in t.lines) == 3_000
    assert t.inventory_value == 100_000 + 3_000
    assert t.total == 103_000


def test_purchase_discount():
    lines = [PurchaseLine(1, 10_000, 5_000, discount=5_000)]
    t = compute_purchase(lines, 0, TaxMode.NONE)
    assert t.subtotal == 45_000 and t.discount_total == 5_000


def test_exclusive_tax_recoverable():
    lines = [PurchaseLine(1, 10_000, 5_000)]
    t = compute_purchase(lines, 0, TaxMode.EXCLUSIVE, default_tax_bp=1500, tax_recoverable=True)
    assert t.tax == 7_500 and t.total == 57_500
    assert t.inventory_value == 50_000  # recoverable tax excluded from cost


def test_exclusive_tax_non_recoverable():
    lines = [PurchaseLine(1, 10_000, 5_000)]
    t = compute_purchase(lines, 0, TaxMode.EXCLUSIVE, default_tax_bp=1500, tax_recoverable=False)
    assert t.inventory_value == 57_500  # tax capitalized into cost


def test_empty_purchase():
    with pytest.raises(ValidationError):
        compute_purchase([], 0, TaxMode.NONE)
