"""FIFO payment allocation to open documents, with advance remainder (pure)."""

from __future__ import annotations

from dataclasses import dataclass

from vybora.core.errors import ValidationError


@dataclass(frozen=True)
class OpenDocument:
    document_id: int
    due: int  # poisha outstanding, > 0


@dataclass(frozen=True)
class Allocation:
    document_id: int
    amount: int


@dataclass
class AllocationResult:
    allocations: list[Allocation]
    advance: int  # excess beyond all open dues


def allocate_fifo(amount: int, open_documents: list[OpenDocument]) -> AllocationResult:
    """Allocate amount to oldest documents first (input order = oldest first).

    Excess becomes an advance. Documents must be pre-sorted oldest-first by caller.
    """
    if amount <= 0:
        raise ValidationError("পরিশোধের পরিমাণ অবশ্যই ধনাত্মক হতে হবে।")
    remaining = amount
    allocations: list[Allocation] = []
    for doc in open_documents:
        if remaining <= 0:
            break
        if doc.due <= 0:
            continue
        take = min(remaining, doc.due)
        allocations.append(Allocation(doc.document_id, take))
        remaining -= take
    return AllocationResult(allocations=allocations, advance=remaining)
