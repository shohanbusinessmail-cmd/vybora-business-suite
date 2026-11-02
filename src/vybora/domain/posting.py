"""Pure double-entry posting builders (see docs/accounting/ACCOUNTING_SPEC.md).

Each returns a list[JournalLine] that the service persists in the same transaction as
the source document. All amounts integer poisha. Builders never produce unbalanced
entries for valid inputs; the service validates balance before commit regardless.
"""

from __future__ import annotations

from vybora.core.errors import ValidationError
from vybora.domain import accounting as acc
from vybora.domain.accounting import JournalLine, line


def sale_posting(
    *,
    total: int,
    tax: int,
    paid: int,
    due: int,
    cogs: int,
    cash_account: str,
    customer_id: int | None,
    advance_applied: int = 0,
) -> list[JournalLine]:
    """Cash/credit/partial sale. Revenue is net of tax; discounts already netted.

    advance_applied draws down the Customer Advances liability to cover part of the
    due, so only (due - advance_applied) goes to Accounts Receivable.
    """
    if total < 0 or paid < 0 or due < 0 or cogs < 0 or tax < 0:
        raise ValidationError("বিক্রয় পোস্টিং মান ঋণাত্মক হতে পারবে না।")
    if paid + due != total:
        raise ValidationError("বিক্রয় পোস্টিং: পরিশোধিত + বাকি ≠ মোট।")
    lines: list[JournalLine] = []
    cash_portion = paid
    if cash_portion > 0:
        lines.append(line(cash_account, debit=cash_portion))
    ar_portion = due - advance_applied
    if ar_portion < 0:
        raise ValidationError("অগ্রিম প্রয়োগ বাকির চেয়ে বেশি হতে পারবে না।")
    if advance_applied > 0:
        lines.append(
            line(
                acc.CUSTOMER_ADVANCES,
                debit=advance_applied,
                party_type="customer",
                party_id=customer_id,
            )
        )
    if ar_portion > 0:
        lines.append(
            line(
                acc.ACCOUNTS_RECEIVABLE,
                debit=ar_portion,
                party_type="customer",
                party_id=customer_id,
            )
        )
    net_revenue = total - tax
    if net_revenue > 0:
        lines.append(line(acc.SALES_REVENUE, credit=net_revenue))
    if tax > 0:
        lines.append(line(acc.VAT_PAYABLE, credit=tax))
    if cogs > 0:
        lines.append(line(acc.COGS, debit=cogs))
        lines.append(line(acc.INVENTORY, credit=cogs))
    return lines


def collection_posting(
    *, amount: int, allocated: int, advance: int, cash_account: str, customer_id: int
) -> list[JournalLine]:
    if amount <= 0 or allocated < 0 or advance < 0 or allocated + advance != amount:
        raise ValidationError("গ্রাহক পরিশোধ পোস্টিং ভারসাম্যপূর্ণ নয়।")
    lines = [line(cash_account, debit=amount)]
    if allocated > 0:
        lines.append(
            line(
                acc.ACCOUNTS_RECEIVABLE,
                credit=allocated,
                party_type="customer",
                party_id=customer_id,
            )
        )
    if advance > 0:
        lines.append(
            line(acc.CUSTOMER_ADVANCES, credit=advance, party_type="customer", party_id=customer_id)
        )
    return lines


def purchase_posting(
    *,
    inventory_value: int,
    tax: int,
    paid: int,
    due: int,
    cash_account: str,
    supplier_id: int,
    tax_recoverable: bool = True,
) -> list[JournalLine]:
    lines: list[JournalLine] = []
    if inventory_value > 0:
        lines.append(line(acc.INVENTORY, debit=inventory_value))
    if tax > 0 and tax_recoverable:
        lines.append(line(acc.VAT_RECEIVABLE, debit=tax))
    if paid > 0:
        lines.append(line(cash_account, credit=paid))
    if due > 0:
        lines.append(
            line(acc.ACCOUNTS_PAYABLE, credit=due, party_type="supplier", party_id=supplier_id)
        )
    return lines


def supplier_payment_posting(
    *, amount: int, allocated: int, advance: int, cash_account: str, supplier_id: int
) -> list[JournalLine]:
    if amount <= 0 or allocated < 0 or advance < 0 or allocated + advance != amount:
        raise ValidationError("সরবরাহকারী পরিশোধ পোস্টিং ভারসাম্যপূর্ণ নয়।")
    lines: list[JournalLine] = []
    if allocated > 0:
        lines.append(
            line(acc.ACCOUNTS_PAYABLE, debit=allocated, party_type="supplier", party_id=supplier_id)
        )
    if advance > 0:
        lines.append(
            line(acc.SUPPLIER_ADVANCES, debit=advance, party_type="supplier", party_id=supplier_id)
        )
    lines.append(line(cash_account, credit=amount))
    return lines


def sale_return_posting(
    *,
    refund_net: int,
    refund_tax: int,
    refund_paid: int,
    credit_to_due: int,
    restock_value: int,
    cash_account: str,
    customer_id: int | None,
) -> list[JournalLine]:
    if refund_paid + credit_to_due != refund_net + refund_tax:
        raise ValidationError("বিক্রয় ফেরত পোস্টিং ভারসাম্যপূর্ণ নয়।")
    lines: list[JournalLine] = []
    if refund_net > 0:
        lines.append(line(acc.SALES_RETURNS, debit=refund_net))
    if refund_tax > 0:
        lines.append(line(acc.VAT_PAYABLE, debit=refund_tax))
    if refund_paid > 0:
        lines.append(line(cash_account, credit=refund_paid))
    if credit_to_due > 0:
        lines.append(
            line(
                acc.ACCOUNTS_RECEIVABLE,
                credit=credit_to_due,
                party_type="customer",
                party_id=customer_id,
            )
        )
    if restock_value > 0:
        lines.append(line(acc.INVENTORY, debit=restock_value))
        lines.append(line(acc.COGS, credit=restock_value))
    return lines


def purchase_return_posting(
    *,
    cost_value: int,
    tax_value: int,
    credit_amount: int,
    refund_amount: int,
    variance: int,
    cash_account: str,
    supplier_id: int,
    tax_recoverable: bool = True,
) -> list[JournalLine]:
    lines: list[JournalLine] = []
    total_received = credit_amount + refund_amount
    if total_received <= 0:
        raise ValidationError("ক্রয় ফেরতের পরিমাণ ধনাত্মক হতে হবে।")
    if credit_amount > 0:
        lines.append(
            line(
                acc.ACCOUNTS_PAYABLE,
                debit=credit_amount,
                party_type="supplier",
                party_id=supplier_id,
            )
        )
    if refund_amount > 0:
        lines.append(line(cash_account, debit=refund_amount))
    if cost_value > 0:
        lines.append(line(acc.INVENTORY, credit=cost_value))
    if tax_value > 0 and tax_recoverable:
        lines.append(line(acc.VAT_RECEIVABLE, credit=tax_value))
    # variance = original_cost - removed_value >= 0: supplier credits more than the
    # book value removed -> gain. (Negative variance would be a loss.)
    if variance > 0:
        lines.append(line(acc.INVENTORY_ADJUST_GAIN, credit=variance))
    elif variance < 0:
        lines.append(line(acc.INVENTORY_ADJUST_LOSS, debit=-variance))
    return lines


def expense_posting(*, amount: int, expense_account: str, cash_account: str) -> list[JournalLine]:
    if amount <= 0:
        raise ValidationError("ব্যয়ের পরিমাণ ধনাত্মক হতে হবে।")
    return [line(expense_account, debit=amount), line(cash_account, credit=amount)]


def other_income_posting(*, amount: int, cash_account: str, kind: str) -> list[JournalLine]:
    if amount <= 0:
        raise ValidationError("আয়ের পরিমাণ ধনাত্মক হতে হবে।")
    if kind == "income":
        return [line(cash_account, debit=amount), line(acc.OTHER_INCOME, credit=amount)]
    if kind == "loan":
        return [line(cash_account, debit=amount), line(acc.LOAN_PAYABLE, credit=amount)]
    if kind == "capital":
        return [line(cash_account, debit=amount), line(acc.OWNER_CAPITAL, credit=amount)]
    raise ValidationError("অন্যান্য আয়ের ধরন অবৈধ।")


def cash_transfer_posting(*, amount: int, from_account: str, to_account: str) -> list[JournalLine]:
    if amount <= 0 or from_account == to_account:
        raise ValidationError("স্থানান্তর পোস্টিং অবৈধ।")
    return [line(to_account, debit=amount), line(from_account, credit=amount)]


def adjustment_posting(*, value_delta: int, write_off: bool = False) -> list[JournalLine]:
    if value_delta == 0:
        raise ValidationError("সমন্বয়ের মান শূন্য হতে পারবে না।")
    if value_delta > 0:
        return [
            line(acc.INVENTORY, debit=value_delta),
            line(acc.INVENTORY_ADJUST_GAIN, credit=value_delta),
        ]
    expense = acc.WRITE_OFF if write_off else acc.INVENTORY_ADJUST_LOSS
    return [line(expense, debit=-value_delta), line(acc.INVENTORY, credit=-value_delta)]


def opening_balance_posting(
    *,
    kind: str,
    amount: int,
    party_type: str | None = None,
    party_id: int | None = None,
    cash_account: str = acc.CASH,
) -> list[JournalLine]:
    if amount <= 0:
        raise ValidationError("প্রারম্ভিক জের ধনাত্মক হতে হবে।")
    eq = acc.OPENING_BALANCE_EQUITY
    if kind == "customer_receivable":
        return [
            line(acc.ACCOUNTS_RECEIVABLE, debit=amount, party_type=party_type, party_id=party_id),
            line(eq, credit=amount),
        ]
    if kind == "supplier_payable":
        return [
            line(eq, debit=amount),
            line(acc.ACCOUNTS_PAYABLE, credit=amount, party_type=party_type, party_id=party_id),
        ]
    if kind == "inventory":
        return [line(acc.INVENTORY, debit=amount), line(eq, credit=amount)]
    if kind in ("cash", "bank"):
        return [line(cash_account, debit=amount), line(eq, credit=amount)]
    raise ValidationError("প্রারম্ভিক জেরের ধরন অবৈধ।")


def cash_variance_posting(*, variance: int) -> list[JournalLine]:
    if variance == 0:
        return []
    if variance > 0:
        return [line(acc.CASH, debit=variance), line(acc.CASH_OVER, credit=variance)]
    return [line(acc.CASH_SHORT, debit=-variance), line(acc.CASH, credit=-variance)]
