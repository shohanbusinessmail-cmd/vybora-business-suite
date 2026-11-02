import pytest

from vybora.core.errors import ValidationError
from vybora.domain import accounting as acc
from vybora.domain import posting
from vybora.domain.accounting import JournalEntry, JournalLine, balanced


def assert_balanced(lines):
    assert balanced(lines), f"unbalanced: {lines}"
    e = JournalEntry("2026-11-02", "test", 1, "test", lines)
    e.validate()


def test_cash_sale_balanced():
    lines = posting.sale_posting(
        total=23_000,
        tax=0,
        paid=23_000,
        due=0,
        cogs=15_000,
        cash_account=acc.CASH,
        customer_id=None,
    )
    assert_balanced(lines)
    assert sum(ln.debit for ln in lines) == 23_000 + 15_000


def test_credit_sale_balanced():
    lines = posting.sale_posting(
        total=10_000, tax=0, paid=4_000, due=6_000, cogs=5_000, cash_account=acc.CASH, customer_id=7
    )
    assert_balanced(lines)
    ar = [ln for ln in lines if ln.account_code == acc.ACCOUNTS_RECEIVABLE]
    assert ar[0].debit == 6_000 and ar[0].party_id == 7


def test_sale_with_tax_and_advance():
    lines = posting.sale_posting(
        total=11_500,
        tax=1_500,
        paid=5_000,
        due=6_500,
        cogs=5_000,
        cash_account=acc.CASH,
        customer_id=7,
        advance_applied=2_000,
    )
    assert_balanced(lines)
    adv = [ln for ln in lines if ln.account_code == acc.CUSTOMER_ADVANCES]
    assert adv[0].debit == 2_000
    ar = [ln for ln in lines if ln.account_code == acc.ACCOUNTS_RECEIVABLE]
    assert ar[0].debit == 4_500


def test_sale_mismatch_rejected():
    with pytest.raises(ValidationError):
        posting.sale_posting(
            total=10_000,
            tax=0,
            paid=4_000,
            due=5_000,
            cogs=0,
            cash_account=acc.CASH,
            customer_id=None,
        )


def test_collection_balanced():
    lines = posting.collection_posting(
        amount=5_000, allocated=3_000, advance=2_000, cash_account=acc.CASH, customer_id=7
    )
    assert_balanced(lines)


def test_purchase_balanced():
    lines = posting.purchase_posting(
        inventory_value=50_000,
        tax=7_500,
        paid=20_000,
        due=37_500,
        cash_account=acc.CASH,
        supplier_id=3,
    )
    assert_balanced(lines)


def test_supplier_payment_balanced():
    lines = posting.supplier_payment_posting(
        amount=10_000, allocated=8_000, advance=2_000, cash_account=acc.CASH, supplier_id=3
    )
    assert_balanced(lines)


def test_sale_return_balanced():
    lines = posting.sale_return_posting(
        refund_net=7_667,
        refund_tax=0,
        refund_paid=7_667,
        credit_to_due=0,
        restock_value=5_000,
        cash_account=acc.CASH,
        customer_id=7,
    )
    assert_balanced(lines)


def test_purchase_return_with_variance_balanced():
    lines = posting.purchase_return_posting(
        cost_value=10_000,
        tax_value=0,
        credit_amount=25_000,
        refund_amount=0,
        variance=15_000,
        cash_account=acc.CASH,
        supplier_id=3,
    )
    assert_balanced(lines)
    gain = [ln for ln in lines if ln.account_code == acc.INVENTORY_ADJUST_GAIN]
    assert gain[0].credit == 15_000


def test_expense_and_income():
    assert_balanced(
        posting.expense_posting(amount=5_000, expense_account="6000", cash_account=acc.CASH)
    )
    assert_balanced(
        posting.other_income_posting(amount=5_000, cash_account=acc.CASH, kind="income")
    )
    assert_balanced(posting.other_income_posting(amount=5_000, cash_account=acc.CASH, kind="loan"))
    assert_balanced(
        posting.other_income_posting(amount=5_000, cash_account=acc.CASH, kind="capital")
    )


def test_loan_is_not_income():
    lines = posting.other_income_posting(amount=5_000, cash_account=acc.CASH, kind="loan")
    assert not any(ln.account_code == acc.OTHER_INCOME for ln in lines)
    assert any(ln.account_code == acc.LOAN_PAYABLE for ln in lines)


def test_transfer_not_income():
    lines = posting.cash_transfer_posting(amount=5_000, from_account=acc.CASH, to_account=acc.BANK)
    assert_balanced(lines)
    assert not any(ln.account_code in (acc.OTHER_INCOME, acc.SALES_REVENUE) for ln in lines)


def test_adjustment_up_down():
    assert_balanced(posting.adjustment_posting(value_delta=10_000))
    assert_balanced(posting.adjustment_posting(value_delta=-10_000, write_off=True))


def test_opening_balances():
    for kind in ("customer_receivable", "supplier_payable", "inventory", "cash", "bank"):
        assert_balanced(
            posting.opening_balance_posting(
                kind=kind, amount=5_000, party_type="customer", party_id=1
            )
        )


def test_cash_variance():
    assert_balanced(posting.cash_variance_posting(variance=500))
    assert_balanced(posting.cash_variance_posting(variance=-500))
    assert posting.cash_variance_posting(variance=0) == []


def test_journal_line_both_sides_rejected():
    with pytest.raises(ValidationError):
        JournalLine(acc.CASH, debit=100, credit=100)


def test_journal_line_neither_side_rejected():
    with pytest.raises(ValidationError):
        JournalLine(acc.CASH, debit=0, credit=0)


def test_unbalanced_entry_rejected():
    e = JournalEntry(
        "2026-11-02",
        "test",
        1,
        "t",
        [JournalLine(acc.CASH, debit=100), JournalLine(acc.SALES_REVENUE, credit=90)],
    )
    with pytest.raises(ValidationError):
        e.validate()
