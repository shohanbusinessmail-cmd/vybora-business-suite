from datetime import date

from vybora.core.formatting import (
    BN_DIGITS,
    DisplayPrefs,
    format_date,
    format_money,
    format_percent,
    format_quantity,
    to_bengali_digits,
)


def test_bengali_digits():
    assert len(BN_DIGITS) == 10
    assert to_bengali_digits("0123456789") == BN_DIGITS
    # Each ASCII digit maps to the corresponding Bengali digit.
    for i, ch in enumerate(BN_DIGITS):
        assert to_bengali_digits(str(i)) == ch


def test_format_money_default_bengali():
    p = DisplayPrefs()
    assert format_money(123450, p) == "৳১,২৩৪.৫০"
    assert format_money(0, p) == "৳০.০০"
    assert format_money(-525, p) == "-৳৫.২৫"


def test_format_money_international():
    p = DisplayPrefs(bengali_digits=False)
    # 1234567 poisha = 12345.67 BDT; South-Asian grouping -> 12,345.67
    assert format_money(1234567, p) == "৳12,345.67"
    # 123456789 poisha = 1234567.89 BDT -> 12,34,567.89
    assert format_money(123456789, p) == "৳12,34,567.89"


def test_format_money_suffix():
    p = DisplayPrefs(currency_prefix=False, bengali_digits=False)
    assert format_money(10000, p) == "100.00 ৳"


def test_format_money_no_separator():
    p = DisplayPrefs(thousand_separator=False, bengali_digits=False)
    assert format_money(1234567, p) == "৳12345.67"


def test_format_quantity():
    p = DisplayPrefs(bengali_digits=False)
    assert format_quantity(1500, True, p) == "1.5"
    assert format_quantity(2000, False, p) == "2"


def test_format_date():
    p = DisplayPrefs(bengali_digits=False)
    assert format_date(date(2026, 11, 2), p) == "02/11/2026"
    p2 = DisplayPrefs(bengali_digits=False, date_format="yyyy-mm-dd")
    assert format_date("2026-11-02", p2) == "2026-11-02"


def test_format_percent():
    p = DisplayPrefs(bengali_digits=False)
    assert format_percent(1500, p) == "15%"
    assert format_percent(750, p) == "7.5%"
    assert format_percent(0, p) == "0%"


def test_display_does_not_mutate_value():
    p = DisplayPrefs()
    v = 123450
    format_money(v, p)
    assert v == 123450
