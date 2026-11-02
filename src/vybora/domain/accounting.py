"""Double-entry accounting primitives and posting-rule builders (pure).

All amounts are integer poisha. Every journal must balance (sum debit == sum credit).
Posting builders return lists of JournalLine; the service layer persists them inside
the same transaction as the source business document.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from vybora.core.errors import ValidationError


class AccountType(StrEnum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    INCOME = "INCOME"
    COGS = "COGS"
    EXPENSE = "EXPENSE"


# Stable system account codes (see docs/accounting/ACCOUNTING_SPEC.md).
CASH = "1000"
BANK = "1010"
ACCOUNTS_RECEIVABLE = "1100"
SUPPLIER_ADVANCES = "1150"
INVENTORY = "1200"
VAT_RECEIVABLE = "1300"
ACCOUNTS_PAYABLE = "2000"
VAT_PAYABLE = "2100"
LOAN_PAYABLE = "2200"
CUSTOMER_ADVANCES = "2300"
OWNER_CAPITAL = "3000"
OPENING_BALANCE_EQUITY = "3900"
SALES_REVENUE = "4000"
SALES_DISCOUNTS = "4100"
SALES_RETURNS = "4200"
OTHER_INCOME = "4900"
CASH_OVER = "4950"
COGS = "5000"
INVENTORY_ADJUST_LOSS = "5100"
WRITE_OFF = "5200"
INVENTORY_ADJUST_GAIN = "5900"
CASH_SHORT = "6995"


@dataclass(frozen=True)
class AccountDef:
    code: str
    name_bn: str
    type: AccountType
    is_system: bool = True


SYSTEM_ACCOUNTS: list[AccountDef] = [
    AccountDef(CASH, "নগদ তহবিল", AccountType.ASSET),
    AccountDef(BANK, "ব্যাংক হিসাব", AccountType.ASSET),
    AccountDef(ACCOUNTS_RECEIVABLE, "গ্রাহক পাওনা", AccountType.ASSET),
    AccountDef(SUPPLIER_ADVANCES, "সরবরাহকারী অগ্রিম", AccountType.ASSET),
    AccountDef(INVENTORY, "পণ্য মজুত", AccountType.ASSET),
    AccountDef(VAT_RECEIVABLE, "ভ্যাট Receivable", AccountType.ASSET),
    AccountDef(ACCOUNTS_PAYABLE, "সরবরাহকারী প্রদেয়", AccountType.LIABILITY),
    AccountDef(VAT_PAYABLE, "ভ্যাট প্রদেয়", AccountType.LIABILITY),
    AccountDef(LOAN_PAYABLE, "ঋণ প্রদেয়", AccountType.LIABILITY),
    AccountDef(CUSTOMER_ADVANCES, "গ্রাহক অগ্রিম", AccountType.LIABILITY),
    AccountDef(OWNER_CAPITAL, "মূলধন", AccountType.EQUITY),
    AccountDef(OPENING_BALANCE_EQUITY, "প্রারম্ভিক জের ভারসাম্য", AccountType.EQUITY),
    AccountDef(SALES_REVENUE, "বিক্রয় আয়", AccountType.INCOME),
    AccountDef(SALES_DISCOUNTS, "বিক্রয় ছাড়", AccountType.INCOME),
    AccountDef(SALES_RETURNS, "বিক্রয় ফেরত", AccountType.INCOME),
    AccountDef(OTHER_INCOME, "অন্যান্য আয়", AccountType.INCOME),
    AccountDef(CASH_OVER, "নগদ উদ্বৃত্ত", AccountType.INCOME),
    AccountDef(COGS, "বিক্রীত পণ্যের ব্যয়", AccountType.COGS),
    AccountDef(INVENTORY_ADJUST_LOSS, "মজুত সমন্বয় ব্যয়", AccountType.COGS),
    AccountDef(WRITE_OFF, "ক্ষতিগ্রস্ত/মেয়াদোত্তীর্ণ অপচয়", AccountType.COGS),
    AccountDef(INVENTORY_ADJUST_GAIN, "মজুত সমন্বয় আয়", AccountType.COGS),
    AccountDef(CASH_SHORT, "নগদ ঘাটতি", AccountType.EXPENSE),
]


@dataclass(frozen=True)
class JournalLine:
    account_code: str
    debit: int = 0
    credit: int = 0
    party_type: str | None = None  # 'customer' | 'supplier'
    party_id: int | None = None

    def __post_init__(self):
        if self.debit < 0 or self.credit < 0:
            raise ValidationError("জার্নালের ডেবিট/ক্রেডিট ঋণাত্মক হতে পারবে না।")
        if (self.debit > 0) == (self.credit > 0):
            raise ValidationError("প্রতিটি জার্নাল লাইনে কেবল ডেবিট অথবা ক্রেডিট থাকতে হবে।")


@dataclass
class JournalEntry:
    date: str
    source_type: str
    source_id: int | None
    memo: str
    lines: list[JournalLine] = field(default_factory=list)

    @property
    def total_debit(self) -> int:
        return sum(ln.debit for ln in self.lines)

    @property
    def total_credit(self) -> int:
        return sum(ln.credit for ln in self.lines)

    def validate(self) -> None:
        if len(self.lines) < 2:
            raise ValidationError("জার্নাল এন্ট্রিতে কমপক্ষে দুটি লাইন থাকতে হবে।")
        if self.total_debit != self.total_credit:
            raise ValidationError("জার্নাল এন্ট্রি ভারসাম্যপূর্ণ নয় (ডেবিট ≠ ক্রেডিট)।")
        if self.total_debit == 0:
            raise ValidationError("জার্নাল এন্ট্রির পরিমাণ শূন্য হতে পারবে না।")


def line(
    account: str,
    *,
    debit: int = 0,
    credit: int = 0,
    party_type: str | None = None,
    party_id: int | None = None,
) -> JournalLine:
    return JournalLine(account, debit, credit, party_type, party_id)


def balanced(lines: list[JournalLine]) -> bool:
    return sum(ln.debit for ln in lines) == sum(ln.credit for ln in lines)
