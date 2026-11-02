"""Moving weighted-average inventory costing via the value-pool method (ADR-004).

Pool = (stock_qty milli-units, stock_value poisha). COGS is computed at sale time and
the pool reduced by exactly that amount, so remaining_value + sum(COGS) == original
value with no rounding drift. Historical costs are never rewritten.
"""

from __future__ import annotations

from dataclasses import dataclass

from vybora.core.errors import ValidationError
from vybora.core.money import round_half_up


@dataclass
class StockPool:
    qty: int = 0  # milli-units
    value: int = 0  # poisha
    last_avg_cost: int = 0  # poisha per whole unit (cache for display/negative-stock)

    def avg_cost_per_unit(self) -> int:
        if self.qty <= 0:
            return self.last_avg_cost
        return round_half_up(self.value * 1000, self.qty)


def apply_purchase(pool: StockPool, qty: int, landed_cost: int) -> StockPool:
    if qty <= 0:
        raise ValidationError("ক্রয়ের পরিমাণ অবশ্যই ধনাত্মক হতে হবে।")
    if landed_cost < 0:
        raise ValidationError("ক্রয় মূল্য ঋণাত্মক হতে পারবে না।")
    pool.qty += qty
    pool.value += landed_cost
    pool.last_avg_cost = pool.avg_cost_per_unit()
    return pool


def compute_cogs(
    pool: StockPool, qty: int, *, allow_negative: bool = False
) -> tuple[int, StockPool]:
    """Return (cogs_poisha, updated_pool) for selling qty from the pool."""
    if qty <= 0:
        raise ValidationError("বিক্রয়ের পরিমাণ অবশ্যই ধনাত্মক হতে হবে।")
    if pool.qty <= 0:
        if not allow_negative:
            raise ValidationError("পর্যাপ্ত মজুত নেই।")
        cogs = round_half_up(pool.last_avg_cost * qty, 1000)
        pool.qty -= qty
        pool.value -= cogs
        return cogs, pool
    if qty > pool.qty and not allow_negative:
        raise ValidationError("পর্যাপ্ত মজুত নেই।")
    cogs = round_half_up(pool.value * qty, pool.qty)
    pool.qty -= qty
    pool.value -= cogs
    if pool.qty > 0:
        pool.last_avg_cost = pool.avg_cost_per_unit()
    return cogs, pool


def apply_sale_return(pool: StockPool, qty: int, original_cogs_share: int) -> StockPool:
    if qty <= 0:
        raise ValidationError("ফেরতের পরিমাণ অবশ্যই ধনাত্মক হতে হবে।")
    if original_cogs_share < 0:
        raise ValidationError("ফেরত মূল্য ঋণাত্মক হতে পারবে না।")
    pool.qty += qty
    pool.value += original_cogs_share
    if pool.qty > 0:
        pool.last_avg_cost = pool.avg_cost_per_unit()
    return pool


def apply_purchase_return(
    pool: StockPool, qty: int, original_cost_share: int
) -> tuple[int, int, StockPool]:
    """Return (removed_value, variance_to_adjust, updated_pool).

    Removes value at original purchase cost, capped so the pool value cannot go
    negative while qty stays >= 0; any shortfall is a variance to the adjustment acct.
    """
    if qty <= 0:
        raise ValidationError("ফেরতের পরিমাণ অবশ্যই ধনাত্মক হতে হবে।")
    if qty > pool.qty:
        raise ValidationError("মজুতের চেয়ে বেশি ক্রয় ফেরত দেয়া যায় না।")
    desired = original_cost_share
    removed = min(pool.value, desired) if pool.qty - qty >= 0 else desired
    variance = desired - removed
    pool.qty -= qty
    pool.value -= removed
    if pool.qty > 0:
        pool.last_avg_cost = pool.avg_cost_per_unit()
    return removed, variance, pool


def apply_adjustment(
    pool: StockPool, qty_delta: int, reference_cost_per_unit: int
) -> tuple[int, StockPool]:
    """Return (value_delta, updated_pool). Positive qty adds at reference cost;
    negative qty removes proportional pool value."""
    if qty_delta == 0:
        raise ValidationError("সমন্বয়ের পরিমাণ শূন্য হতে পারবে না।")
    if qty_delta > 0:
        value_delta = round_half_up(reference_cost_per_unit * qty_delta, 1000)
        pool.qty += qty_delta
        pool.value += value_delta
    else:
        q = -qty_delta
        if q > pool.qty:
            raise ValidationError("মজুতের চেয়ে বেশি কমানো যায় না।")
        value_delta = -round_half_up(pool.value * q, pool.qty) if pool.qty > 0 else 0
        pool.qty -= q
        pool.value += value_delta
    if pool.qty > 0:
        pool.last_avg_cost = pool.avg_cost_per_unit()
    return value_delta, pool
