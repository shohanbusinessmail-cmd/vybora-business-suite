import pytest

from vybora.core.errors import ValidationError
from vybora.domain.inventory import (
    StockPool,
    apply_adjustment,
    apply_purchase,
    apply_purchase_return,
    apply_sale_return,
    compute_cogs,
)


def test_purchase_then_sale_cogs_exact():
    pool = StockPool()
    apply_purchase(pool, 10_000, 50_000)  # 10 pcs @ 50 = 500.00
    assert pool.qty == 10_000 and pool.value == 50_000
    cogs, pool = compute_cogs(pool, 3_000)  # sell 3
    assert cogs == 15_000
    assert pool.qty == 7_000 and pool.value == 35_000


def test_weighted_average_two_purchases():
    pool = StockPool()
    apply_purchase(pool, 10_000, 50_000)  # 10 @ 50
    apply_purchase(pool, 10_000, 70_000)  # 10 @ 70 -> avg 60
    assert pool.avg_cost_per_unit() == 6_000
    cogs, pool = compute_cogs(pool, 5_000)  # sell 5 @ avg 60 = 300
    assert cogs == 30_000
    assert pool.value == 90_000 and pool.qty == 15_000


def test_no_rounding_drift_full_sell():
    pool = StockPool()
    apply_purchase(pool, 3_000, 10_000)  # 3 pcs, 100.00 total (avg 33.33)
    total_cogs = 0
    for _ in range(3):
        cogs, pool = compute_cogs(pool, 1_000)
        total_cogs += cogs
    assert pool.qty == 0 and pool.value == 0
    assert total_cogs == 10_000  # exact, no drift


def test_insufficient_stock_raises():
    pool = StockPool(qty=1_000, value=5_000)
    with pytest.raises(ValidationError):
        compute_cogs(pool, 2_000)


def test_negative_stock_policy():
    pool = StockPool(qty=0, value=0, last_avg_cost=5_000)
    cogs, pool = compute_cogs(pool, 2_000, allow_negative=True)
    assert cogs == 10_000
    assert pool.qty == -2_000


def test_sale_return_restocks_at_original_cogs():
    pool = StockPool()
    apply_purchase(pool, 10_000, 50_000)
    cogs, pool = compute_cogs(pool, 3_000)  # 15000
    apply_sale_return(pool, 1_000, 5_000)  # return 1 at original share 5000
    assert pool.qty == 8_000 and pool.value == 40_000


def test_purchase_return_variance():
    pool = StockPool()
    apply_purchase(pool, 10_000, 50_000)  # avg 50
    apply_purchase(pool, 10_000, 30_000)  # avg now 40
    # return 5 of the FIRST purchase at original cost 50 -> 25000 desired
    removed, variance, pool = apply_purchase_return(pool, 5_000, 25_000)
    # pool value 80000, qty 20000; removing 5000 at desired 25000 (<= value) -> no cap
    assert removed == 25_000 and variance == 0
    assert pool.qty == 15_000 and pool.value == 55_000


def test_purchase_return_capped_variance():
    pool = StockPool(qty=5_000, value=10_000)  # avg 20
    removed, variance, pool = apply_purchase_return(pool, 5_000, 25_000)
    assert removed == 10_000 and variance == 15_000
    assert pool.qty == 0 and pool.value == 0


def test_adjustment_up_down():
    pool = StockPool(qty=10_000, value=50_000)
    delta, pool = apply_adjustment(pool, 2_000, 5_000)
    assert delta == 10_000 and pool.qty == 12_000 and pool.value == 60_000
    delta, pool = apply_adjustment(pool, -2_000, 0)
    assert delta == -10_000 and pool.qty == 10_000 and pool.value == 50_000


def test_adjustment_zero_raises():
    with pytest.raises(ValidationError):
        apply_adjustment(StockPool(qty=1000, value=1000), 0, 0)
