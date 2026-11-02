"""Document number formatting (pure). Allocation is transaction-safe in data layer."""

from __future__ import annotations


def format_number(prefix: str, value: int, padding: int) -> str:
    return f"{prefix}{value:0{padding}d}"
