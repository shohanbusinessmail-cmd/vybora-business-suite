import pytest

from vybora.core.errors import ValidationError
from vybora.domain.sales import CartLine, TaxMode, compute_sale, price_line, validate_payment


def test_simple_sale():
    lines = [CartLine(1, 3_000, 8_000)]  # 3 @ 80 = 240.00
    t = compute_sale(lines, 0, TaxMode.NONE)
    assert t.subtotal == 24_000 and t.total == 24_000 and t.tax == 0


def test_line_and_overall_discount():
    lines = [CartLine(1, 3_000, 8_000, discount=1_000)]  # gross 24000, line 23000
    t = compute_sale(lines, 2_000, TaxMode.NONE)
    assert t.subtotal == 23_000
    assert t.overall_discount == 2_000
    assert t.total == 21_000
    assert t.discount_total == 3_000


def test_overall_discount_allocation_reconciles():
    lines = [CartLine(1, 1_000, 10_000), CartLine(2, 1_000, 20_000)]  # 100 + 200
    t = compute_sale(lines, 1_001, TaxMode.NONE)  # odd discount to test remainder
    assert sum(ln.overall_discount_share for ln in t.lines) == 1_001
    assert t.total == 30_000 - 1_001


def test_exclusive_tax():
    lines = [CartLine(1, 1_000, 10_000)]  # 100.00
    t = compute_sale(lines, 0, TaxMode.EXCLUSIVE, default_tax_bp=1500)  # 15%
    assert t.tax == 1_500 and t.total == 11_500


def test_inclusive_tax():
    lines = [CartLine(1, 1_000, 11_500)]  # 115.00 incl 15%
    t = compute_sale(lines, 0, TaxMode.INCLUSIVE, default_tax_bp=1500)
    assert t.total == 11_500
    assert t.tax == 1_500
    assert t.lines[0].net == 10_000


def test_discount_exceeds_line():
    with pytest.raises(ValidationError):
        price_line(1_000, 10_000, 20_000)


def test_overall_discount_exceeds_subtotal():
    with pytest.raises(ValidationError):
        compute_sale([CartLine(1, 1_000, 10_000)], 20_000, TaxMode.NONE)


def test_empty_cart():
    with pytest.raises(ValidationError):
        compute_sale([], 0, TaxMode.NONE)


def test_validate_payment():
    assert validate_payment(10_000, 10_000, is_credit_allowed=False) == (10_000, 0)
    assert validate_payment(10_000, 4_000, is_credit_allowed=True) == (4_000, 6_000)


def test_overpayment_rejected():
    with pytest.raises(ValidationError):
        validate_payment(10_000, 12_000, is_credit_allowed=True)


def test_credit_without_customer_rejected():
    with pytest.raises(ValidationError):
        validate_payment(10_000, 4_000, is_credit_allowed=False)
