"""Exact money arithmetic in integer poisha (1 BDT = 100 poisha).

No binary floating point is used anywhere in financial paths. Rounding is
half-up (commercial rounding) applied once at defined points.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

POISHA_PER_TAKA = 100


class MoneyError(ValueError):
    """Invalid monetary input."""


def round_half_up(numerator: int, denominator: int) -> int:
    """Round numerator/denominator to nearest integer, halves away from zero.

    Pure integer arithmetic; works for negative values too.
    """
    if denominator == 0:
        raise ZeroDivisionError("denominator must be non-zero")
    if denominator < 0:
        numerator, denominator = -numerator, -denominator
    if numerator >= 0:
        return (2 * numerator + denominator) // (2 * denominator)
    return -((2 * (-numerator) + denominator) // (2 * denominator))


def parse_money(value: str | int | Decimal) -> int:
    """Parse a BDT amount into integer poisha.

    Accepts int (already poisha), Decimal, or a decimal string (e.g. "1234.50").
    More than 2 decimal places are rounded half-up to poisha.
    """
    if isinstance(value, int):
        return value
    try:
        d = Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError) as exc:
        raise MoneyError(f"অবৈধ টাকার পরিমাণ: {value!r}") from exc
    if not d.is_finite():
        raise MoneyError(f"অবৈধ টাকার পরিমাণ: {value!r}")
    return _dec_to_poisha(d)


def _dec_to_poisha(d: Decimal) -> int:
    scaled = d * POISHA_PER_TAKA
    # half-up rounding of a Decimal to integer without float
    sign = -1 if scaled < 0 else 1
    scaled = abs(scaled)
    whole = int(scaled)
    frac = scaled - whole
    if frac >= Decimal("0.5"):
        whole += 1
    return sign * whole


def format_poisha(poisha: int) -> str:
    """Plain decimal string of poisha as BDT with 2 places (no grouping)."""
    sign = "-" if poisha < 0 else ""
    p = abs(poisha)
    return f"{sign}{p // POISHA_PER_TAKA}.{p % POISHA_PER_TAKA:02d}"


def taka_to_poisha(taka: int) -> int:
    return taka * POISHA_PER_TAKA
