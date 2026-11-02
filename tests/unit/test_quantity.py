import pytest

from vybora.core.quantity import QuantityError, format_milli, is_whole, parse_quantity


@pytest.mark.parametrize(
    "value,frac,expected",
    [
        ("1.5", True, 1500),
        ("0.001", True, 1),
        ("2", False, 2000),
        (3, False, 3000),
        ("1.2345", True, 1235),
        ("0.5", True, 500),
    ],
)
def test_parse_quantity(value, frac, expected):
    assert parse_quantity(value, frac) == expected


def test_fraction_rejected_for_whole_unit():
    with pytest.raises(QuantityError):
        parse_quantity("1.5", False)


def test_whole_unit_accepts_integer_string():
    assert parse_quantity("5", False) == 5000


@pytest.mark.parametrize("bad", ["abc", "", "NaN"])
def test_invalid(bad):
    with pytest.raises(QuantityError):
        parse_quantity(bad, True)


def test_format_milli():
    assert format_milli(1500, True) == "1.5"
    assert format_milli(1235, True) == "1.235"
    assert format_milli(2000, False) == "2"
    assert format_milli(500, True) == "0.5"
    assert format_milli(-1500, True) == "-1.5"


def test_is_whole():
    assert is_whole(2000)
    assert not is_whole(1500)
