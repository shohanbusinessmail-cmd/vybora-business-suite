"""Exact quantity arithmetic in integer milli-units (x1000).

Supports fractional units (kg, litre, metre) without binary floating point.
Piece-like units enforce whole quantities.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

MILLI_PER_UNIT = 1000


class QuantityError(ValueError):
    """Invalid quantity input."""


def parse_quantity(value: str | int | Decimal, allows_fraction: bool) -> int:
    """Parse a quantity into integer milli-units.

    int input is treated as whole units. Strings/Decimals are decimal units.
    If the unit does not allow fractions, the result must be a whole unit.
    """
    if isinstance(value, int):
        milli = value * MILLI_PER_UNIT
    else:
        try:
            d = Decimal(str(value).strip().replace(",", ""))
        except (InvalidOperation, ValueError) as exc:
            raise QuantityError(f"অবৈধ পরিমাণ: {value!r}") from exc
        if not d.is_finite():
            raise QuantityError(f"অবৈধ পরিমাণ: {value!r}")
        scaled = d * MILLI_PER_UNIT
        sign = -1 if scaled < 0 else 1
        scaled = abs(scaled)
        whole = int(scaled)
        if scaled - whole >= Decimal("0.5"):
            whole += 1
        milli = sign * whole
    if not allows_fraction and milli % MILLI_PER_UNIT != 0:
        raise QuantityError("এই এককে ভগ্নাংশ পরিমাণ অনুমোদিত নয়")
    return milli


def format_milli(milli: int, allows_fraction: bool) -> str:
    """Plain decimal string of milli-units."""
    sign = "-" if milli < 0 else ""
    m = abs(milli)
    if allows_fraction:
        whole, frac = divmod(m, MILLI_PER_UNIT)
        frac_str = f"{frac:03d}".rstrip("0")
        return f"{sign}{whole}" + (f".{frac_str}" if frac_str else "")
    return f"{sign}{m // MILLI_PER_UNIT}"


def is_whole(milli: int) -> bool:
    return milli % MILLI_PER_UNIT == 0
