"""Bengali-first display formatting for money, quantities, dates and numbers.

Display preferences never alter stored values. Bengali digits: ০১২৩৪৫৬৭৮৯.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from vybora.core.money import format_poisha
from vybora.core.quantity import format_milli

BN_DIGITS = "০১২৩৪৫৬৭৮৯"
_EN_TO_BN = str.maketrans("0123456789", BN_DIGITS)


def to_bengali_digits(text: str) -> str:
    return text.translate(_EN_TO_BN)


@dataclass(frozen=True)
class DisplayPrefs:
    bengali_digits: bool = True
    thousand_separator: bool = True
    decimal_places: int = 2
    currency_symbol: str = "৳"
    currency_prefix: bool = True
    date_format: str = "dd/mm/yyyy"


def _group(integer_part: str) -> str:
    """South-Asian grouping (last 3, then pairs): 12,34,567."""
    if len(integer_part) <= 3:
        return integer_part
    head, tail = integer_part[:-3], integer_part[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])


def format_number(value: int | str, prefs: DisplayPrefs, *, places: int = 0) -> str:
    text = str(value)
    neg = text.startswith("-")
    if neg:
        text = text[1:]
    if "." in text:
        whole, frac = text.split(".", 1)
    else:
        whole, frac = text, ""
    frac = (frac + "0" * places)[:places]
    if prefs.thousand_separator:
        whole = _group(whole)
    out = whole + (f".{frac}" if places else "")
    if neg:
        out = "-" + out
    return to_bengali_digits(out) if prefs.bengali_digits else out


def format_money(poisha: int, prefs: DisplayPrefs | None = None) -> str:
    prefs = prefs or DisplayPrefs()
    base = format_poisha(poisha)
    neg = base.startswith("-")
    if neg:
        base = base[1:]
    whole, frac = base.split(".")
    frac = (frac + "0" * prefs.decimal_places)[: prefs.decimal_places]
    if prefs.thousand_separator:
        whole = _group(whole)
    num = whole + (f".{frac}" if prefs.decimal_places else "")
    if prefs.bengali_digits:
        num = to_bengali_digits(num)
    sym = prefs.currency_symbol
    out = f"{sym}{num}" if prefs.currency_prefix else f"{num} {sym}"
    return ("-" + out) if neg else out


def format_quantity(milli: int, allows_fraction: bool, prefs: DisplayPrefs | None = None) -> str:
    prefs = prefs or DisplayPrefs()
    base = format_milli(milli, allows_fraction)
    return (
        format_number(base, prefs, places=0) if not allows_fraction else _format_frac(base, prefs)
    )


def _format_frac(base: str, prefs: DisplayPrefs) -> str:
    neg = base.startswith("-")
    if neg:
        base = base[1:]
    whole, _, frac = base.partition(".")
    if prefs.thousand_separator:
        whole = _group(whole)
    out = whole + (f".{frac}" if frac else "")
    if prefs.bengali_digits:
        out = to_bengali_digits(out)
    return ("-" + out) if neg else out


def format_date(d: date | datetime | str, prefs: DisplayPrefs | None = None) -> str:
    prefs = prefs or DisplayPrefs()
    if isinstance(d, str):
        d = date.fromisoformat(d[:10])
    if isinstance(d, datetime):
        d = d.date()
    fmt = prefs.date_format.lower()
    if fmt == "mm/dd/yyyy":
        s = f"{d.month:02d}/{d.day:02d}/{d.year:04d}"
    elif fmt == "yyyy-mm-dd":
        s = f"{d.year:04d}-{d.month:02d}-{d.day:02d}"
    else:
        s = f"{d.day:02d}/{d.month:02d}/{d.year:04d}"
    return to_bengali_digits(s) if prefs.bengali_digits else s


def format_percent(basis_points: int, prefs: DisplayPrefs | None = None) -> str:
    """Format basis points (0.01%) as a percent string without floating point."""
    prefs = prefs or DisplayPrefs()
    neg = basis_points < 0
    bp = abs(basis_points)
    whole, frac = divmod(bp, 100)
    base = str(whole) + (f".{frac:02d}".rstrip("0") if frac else "")
    out = _format_frac(base, prefs) if "." in base else format_number(base, prefs, places=0)
    return ("-" if neg else "") + out + "%"
