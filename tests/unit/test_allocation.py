import pytest

from vybora.core.errors import ValidationError
from vybora.domain.allocation import OpenDocument, allocate_fifo


def test_fifo_full_allocation():
    docs = [OpenDocument(1, 3_000), OpenDocument(2, 5_000)]
    r = allocate_fifo(4_000, docs)
    assert r.allocations[0].document_id == 1 and r.allocations[0].amount == 3_000
    assert r.allocations[1].document_id == 2 and r.allocations[1].amount == 1_000
    assert r.advance == 0


def test_excess_becomes_advance():
    docs = [OpenDocument(1, 3_000)]
    r = allocate_fifo(5_000, docs)
    assert r.allocations[0].amount == 3_000
    assert r.advance == 2_000


def test_no_open_docs_all_advance():
    r = allocate_fifo(5_000, [])
    assert r.allocations == [] and r.advance == 5_000


def test_zero_amount_rejected():
    with pytest.raises(ValidationError):
        allocate_fifo(0, [OpenDocument(1, 100)])


def test_allocation_sums_to_amount():
    docs = [OpenDocument(i, 1_000) for i in range(10)]
    r = allocate_fifo(7_500, docs)
    assert sum(a.amount for a in r.allocations) + r.advance == 7_500
