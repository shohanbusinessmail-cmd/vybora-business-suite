"""Sale cart mathematics and validation (pure).

Money in poisha, quantities in milli-units. Tax modes: none / exclusive / inclusive.
Line total = round(qty * unit_price) - line_discount. Overall discount is allocated
across lines proportionally (half-up, remainder to last line) so totals reconcile.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from vybora.core.errors import ValidationError
from vybora.core.money import round_half_up


class TaxMode(StrEnum):
    NONE = "none"
    EXCLUSIVE = "exclusive"
    INCLUSIVE = "inclusive"


@dataclass
class CartLine:
    product_id: int
    qty: int  # milli-units
    unit_price: int  # poisha per whole unit
    discount: int = 0  # poisha, absolute per line
    tax_rate_bp: int = 0  # basis points (0.01%)
    batch_id: int | None = None


@dataclass
class PricedLine:
    product_id: int
    qty: int
    unit_price: int
    discount: int
    gross: int  # round(qty*price/1000)
    line_total: int  # gross - discount (net, excl tax in exclusive/none)
    overall_discount_share: int
    taxable_base: int
    tax: int
    net: int  # final line amount excl tax
    batch_id: int | None = None


@dataclass
class SaleTotals:
    lines: list[PricedLine] = field(default_factory=list)
    subtotal: int = 0  # sum of line_total (after line discounts)
    overall_discount: int = 0
    discount_total: int = 0  # line discounts + overall discount
    tax: int = 0
    total: int = 0  # payable incl tax
    gross_subtotal: int = 0  # sum of gross before any discount


def price_line(qty: int, unit_price: int, discount: int) -> tuple[int, int]:
    if qty <= 0:
        raise ValidationError("পরিমাণ অবশ্যই ধনাত্মক হতে হবে।")
    if unit_price < 0:
        raise ValidationError("একক মূল্য ঋণাত্মক হতে পারবে না।")
    if discount < 0:
        raise ValidationError("ছাড় ঋণাত্মক হতে পারবে না।")
    gross = round_half_up(qty * unit_price, 1000)
    if discount > gross:
        raise ValidationError("ছাড় লাইন মূল্যের চেয়ে বেশি হতে পারবে না।")
    return gross, gross - discount


def compute_sale(
    lines: list[CartLine], overall_discount: int, tax_mode: TaxMode, default_tax_bp: int = 0
) -> SaleTotals:
    if not lines:
        raise ValidationError("বিক্রয়ে কমপক্ষে একটি পণ্য থাকতে হবে।")
    if overall_discount < 0:
        raise ValidationError("ছাড় ঋণাত্মক হতে পারবে না।")

    priced: list[PricedLine] = []
    gross_sum = 0
    subtotal = 0
    for cl in lines:
        bp = cl.tax_rate_bp if cl.tax_rate_bp else default_tax_bp
        gross, line_total = price_line(cl.qty, cl.unit_price, cl.discount)
        gross_sum += gross
        subtotal += line_total
        priced.append(
            PricedLine(
                cl.product_id,
                cl.qty,
                cl.unit_price,
                cl.discount,
                gross,
                line_total,
                0,
                0,
                0,
                0,
                cl.batch_id,
            )
        )

    if overall_discount > subtotal:
        raise ValidationError("সামগ্রিক ছাড় সাবটোটালের চেয়ে বেশি হতে পারবে না।")

    # Allocate overall discount proportionally; remainder to last line.
    allocated = 0
    for i, pl in enumerate(priced):
        if i == len(priced) - 1:
            share = overall_discount - allocated
        else:
            share = round_half_up(overall_discount * pl.line_total, subtotal) if subtotal else 0
            allocated += share
        pl.overall_discount_share = share
        base = pl.line_total - share
        pl.taxable_base = base
        bp = lines[i].tax_rate_bp if lines[i].tax_rate_bp else default_tax_bp
        if tax_mode == TaxMode.EXCLUSIVE:
            pl.tax = round_half_up(base * bp, 10000)
            pl.net = base
        elif tax_mode == TaxMode.INCLUSIVE:
            # base includes tax: net = base / (1 + bp/10000)
            pl.net = round_half_up(base * 10000, 10000 + bp)
            pl.tax = base - pl.net
        else:
            pl.tax = 0
            pl.net = base

    net_sum = sum(pl.net for pl in priced)
    tax_sum = sum(pl.tax for pl in priced)
    if tax_mode == TaxMode.INCLUSIVE:
        total = net_sum + tax_sum  # == subtotal - overall_discount
    else:
        total = net_sum + tax_sum
    return SaleTotals(
        lines=priced,
        subtotal=subtotal,
        overall_discount=overall_discount,
        discount_total=(gross_sum - subtotal) + overall_discount,
        tax=tax_sum,
        total=total,
        gross_subtotal=gross_sum,
    )


def validate_payment(total: int, paid: int, *, is_credit_allowed: bool) -> tuple[int, int]:
    """Return (paid, due). Overpayment at POS is rejected; credit requires customer."""
    if paid < 0:
        raise ValidationError("পরিশোধিত পরিমাণ ঋণাত্মক হতে পারবে না।")
    if paid > total:
        raise ValidationError("পরিশোধিত পরিমাণ মোটের চেয়ে বেশি হতে পারবে না।")
    due = total - paid
    if due > 0 and not is_credit_allowed:
        raise ValidationError("বাকি বিক্রয়ের জন্য গ্রাহক নির্বাচন করুন।")
    return paid, due
