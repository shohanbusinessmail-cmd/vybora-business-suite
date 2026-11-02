from decimal import Decimal

import pytest

from vybora.core.money import (
    MoneyError,
    format_poisha,
    parse_money,
    round_half_up,
    taka_to_poisha,
)


@pytest.mark.parametrize(
    "n,d,expected",
    [
        (5, 2, 3),
        (1, 2, 1),
        (3, 2, 2),
        (1, 3, 0),
        (2, 3, 1),
        (10, 4, 3),
        (15000 * 3, 10, 4500),
        (0, 5, 0),
        (-5, 2, -3),
        (-1, 2, -1),
        (-2, 3, -1),
        (7, 1, 7),
        (100, 100, 1),
    ],
)
def test_round_half_up(n, d, expected):
    assert round_half_up(n, d) == expected


def test_round_half_up_zero_denominator():
    with pytest.raises(ZeroDivisionError):
        round_half_up(1, 0)


def test_round_half_up_negative_denominator():
    assert round_half_up(5, -2) == -3


@pytest.mark.parametrize(
    "value,expected",
    [
        ("1234.50", 123450),
        ("0", 0),
        ("100", 10000),
        ("0.01", 1),
        ("0.005", 1),
        ("0.004", 0),
        ("1,234.50", 123450),
        ("  99.99  ", 9999),
        (500, 500),
        (Decimal("12.34"), 1234),
        ("-5.25", -525),
    ],
)
def test_parse_money(value, expected):
    assert parse_money(value) == expected


@pytest.mark.parametrize("bad", ["abc", "", "NaN", "Infinity", "12.3.4"])
def test_parse_money_invalid(bad):
    with pytest.raises(MoneyError):
        parse_money(bad)


def test_format_poisha():
    assert format_poisha(123450) == "1234.50"
    assert format_poisha(1) == "0.01"
    assert format_poisha(-525) == "-5.25"
    assert format_poisha(0) == "0.00"


def test_taka_to_poisha():
    assert taka_to_poisha(50) == 5000


def test_no_float_drift_large_sum():
    # Summing many 0.10 amounts must be exact (a classic float failure).
    total = sum(parse_money("0.10") for _ in range(100000))
    assert total == 1000000  # 10,000.00 BDT exactly
