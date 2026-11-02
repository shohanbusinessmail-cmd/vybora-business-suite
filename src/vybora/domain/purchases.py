"""Purchase mathematics (pure). Money poisha, qty milli-units.

Landed cost = line net (after discount) + allocated additional cost. Recoverable
input VAT is excluded from inventory cost. Overall additional cost is allocated
proportionally by line net (half-up, remainder to last line).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from vybora.core.errors import ValidationError
from vybora.core.money import round_half_up
from vybora.domain.sales import TaxMode


@dataclass
class PurchaseLine:
    product_id: int
    qty: int
    unit_cost: int  # poisha per whole unit
    discount: int = 0
    tax_rate_bp: int = 0
    batch_id: int | None = None


@dataclass
class CostedLine:
    product_id: int
    qty: int
    unit_cost: int
    discount: int
    gross: int
    line_net: int  # gross - discount
    additional_cost_share: int
    landed_cost: int  # line_net + additional share (inventory value)
    tax: int
    batch_id: int | None = None


@dataclass
class PurchaseTotals:
    lines: list[CostedLine] = field(default_factory=list)
    subtotal: int = 0
    discount_total: int = 0
    additional_cost: int = 0
    tax: int = 0
    total: int = 0  # payable to supplier incl tax
    inventory_value: int = 0  # sum landed_cost (excl recoverable tax)


def compute_purchase(
    lines: list[PurchaseLine],
    additional_cost: int,
    tax_mode: TaxMode,
    default_tax_bp: int = 0,
    *,
    tax_recoverable: bool = True,
) -> PurchaseTotals:
    if not lines:
        raise ValidationError("ক্রয়ে কমপক্ষে একটি পণ্য থাকতে হবে।")
    if additional_cost < 0:
        raise ValidationError("অতিরিক্ত খরচ ঋণাত্মক হতে পারবে না।")
    costed: list[CostedLine] = []
    subtotal = 0
    discount_sum = 0
    for pl in lines:
        if pl.qty <= 0:
            raise ValidationError("পরিমাণ অবশ্যই ধনাত্মক হতে হবে।")
        if pl.unit_cost < 0:
            raise ValidationError("একক ক্রয় মূল্য ঋণাত্মক হতে পারবে না।")
        if pl.discount < 0:
            raise ValidationError("ছাড় ঋণাত্মক হতে পারবে না।")
        gross = round_half_up(pl.qty * pl.unit_cost, 1000)
        if pl.discount > gross:
            raise ValidationError("ছাড় লাইন মূল্যের চেয়ে বেশি হতে পারবে না।")
        net = gross - pl.discount
        subtotal += net
        discount_sum += pl.discount
        costed.append(
            CostedLine(
                pl.product_id, pl.qty, pl.unit_cost, pl.discount, gross, net, 0, 0, 0, pl.batch_id
            )
        )
    allocated = 0
    for i, cl in enumerate(costed):
        share = (
            (additional_cost - allocated)
            if i == len(costed) - 1
            else (round_half_up(additional_cost * cl.line_net, subtotal) if subtotal else 0)
        )
        if i != len(costed) - 1:
            allocated += share
        cl.additional_cost_share = share
        cl.landed_cost = cl.line_net + share
        bp = lines[i].tax_rate_bp if lines[i].tax_rate_bp else default_tax_bp
        if tax_mode == TaxMode.EXCLUSIVE:
            cl.tax = round_half_up(cl.line_net * bp, 10000)
        elif tax_mode == TaxMode.INCLUSIVE:
            net_ex = round_half_up(cl.line_net * 10000, 10000 + bp)
            cl.tax = cl.line_net - net_ex
            cl.landed_cost = net_ex + share
        else:
            cl.tax = 0
    tax_sum = sum(cl.tax for cl in costed)
    inventory_value = sum(cl.landed_cost for cl in costed)
    if tax_mode == TaxMode.EXCLUSIVE:
        total = subtotal + additional_cost + tax_sum
    else:
        total = subtotal + additional_cost
    return PurchaseTotals(
        lines=costed,
        subtotal=subtotal,
        discount_total=discount_sum,
        additional_cost=additional_cost,
        tax=tax_sum,
        total=total,
        inventory_value=inventory_value if tax_recoverable else inventory_value + tax_sum,
    )
