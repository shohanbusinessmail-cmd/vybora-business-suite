# Accounting Specification — Vybora Business Suite

Normative rules for the financial engine. All amounts are integer poisha; quantities
integer milli-units. Rounding: half-up, applied once at the points defined here.

## 1. Chart of accounts (seeded, codes stable)

| Code | Account (bn) | Type | Normal |
|---|---|---|---|
| 1000 | নগদ তহবিল (Cash on Hand) | ASSET | debit |
| 1010 | ব্যাংক হিসাব (Bank) | ASSET | debit |
| 1100 | গ্রাহক পাওনা (Accounts Receivable) | ASSET | debit |
| 1150 | সরবরাহকারী অগ্রিম (Supplier Advances) | ASSET | debit |
| 1200 | পণ্য মজুত (Inventory) | ASSET | debit |
| 1300 | ভ্যাট Receivable (input tax, if enabled) | ASSET | debit |
| 2000 | সরবরাহকারী প্রদেয় (Accounts Payable) | LIABILITY | credit |
| 2100 | ভ্যাট প্রদেয় (VAT Payable) | LIABILITY | credit |
| 2300 | গ্রাহক অগ্রিম (Customer Advances) | LIABILITY | credit |
| 3000 | মূলধন (Owner Capital) | EQUITY | credit |
| 3900 | প্রারম্ভিক জের ভারসাম্য (Opening Balance Equity) | EQUITY | credit |
| 4000 | বিক্রয় আয় (Sales Revenue) | INCOME | credit |
| 4100 | বিক্রয় ছাড় (Sales Discounts, contra) | INCOME | debit |
| 4200 | বিক্রয় ফেরত (Sales Returns, contra) | INCOME | debit |
| 4900 | অন্যান্য আয় (Other Income) | INCOME | credit |
| 4950 | নগদ উদ্বৃত্ত (Cash Over) | INCOME | credit |
| 5000 | বিক্রীত পণ্যের ব্যয় (COGS) | COGS | debit |
| 5100 | মজুত সমন্বয় ব্যয় (Inventory Adjustment Loss) | COGS | debit |
| 5200 | ক্ষতিগ্রস্ত/মেয়াদোত্তীর্ণ অপচয় (Write-off) | COGS | debit |
| 5900 | মজুত সমন্বয় আয় (Inventory Adjustment Gain, contra-COGS) | COGS | credit |
| 6xxx | Operating expense categories (dynamic) | EXPENSE | debit |

Expense categories map 1:1 to expense accounts (6000+). Users may add categories;
accounts are created automatically. System accounts cannot be deleted.

## 2. Journal invariants
- Every entry: Σdebit = Σcredit, ≥ 2 lines, each line exactly one of debit/credit > 0.
- Entry references source document (type + id) and is created in the same transaction.
- Entries are immutable once posted; corrections are reversing entries + new entry.

## 3. Inventory costing (value-pool moving average, ADR-004)
- Pool per product: `stock_qty` (milli), `stock_value` (poisha).
- **Purchase**: qty += q; value += landed_cost_total (net of discount, plus allocated
  additional cost; recoverable input VAT excluded from cost).
- **Sale line COGS** = round_half_up(pool.value × q / pool.qty) when pool.qty > 0.
  Pool.value −= COGS; pool.qty −= q. If policy allows negative stock and pool.qty ≤ 0,
  COGS uses last known average cost (stored `last_avg_cost` per product); the pool may
  go negative in qty and is valued at that average; reconciliation flags negative pools.
- **Sales return (restock)**: qty += q; value += original line COGS share
  (round_half_up(original_line_cogs × return_qty / sold_qty)). Never re-costs history.
- **Purchase return**: remove q at original purchase unit landed cost; value removed =
  min(pool.value, round(original_landed_total × q / purchased_qty)); if pool.value
  would go negative while qty ≥ 0, cap and post variance to 5100. Qty may not go below
  what is physically on hand (validated).
- **Adjustment up**: value += round(q × reference_cost); Dr Inventory / Cr 5900.
  **Adjustment down / write-off**: value −= round(pool.value × q / pool.qty);
  Dr 5100/5200 / Cr Inventory.
- `last_avg_cost` (poisha per whole unit, integer, rounded) is a cache for display and
  negative-stock costing only; the pool is authoritative.

## 4. Posting rules (Dr / Cr)

### 4.1 Sale (total T, discount D, tax X, paid P, due U = T − P, COGS C)
Prices are stored tax-exclusive by default; inclusive mode extracts tax.
```
Dr Cash/Bank (method)      P
Dr Accounts Receivable     U        (if U > 0)
Dr Sales Discounts         D        (if D > 0)
    Cr Sales Revenue       T_gross + X?  → see below
    Cr VAT Payable         X        (if X > 0)
Dr COGS                    C
    Cr Inventory           C
```
Revenue recognition: `Cr Sales Revenue = gross_line_sum − D` (net, excl. tax);
the Sales Discounts contra line is used only in gross-mode reporting; the engine posts
**net revenue** (Cr Sales = T − X) and records D on the sale for reports, so:
Net Sales (P&L) = Sales Revenue − Sales Returns. (Discounts already netted; the
contra account exists for manual journals and future gross-mode option.)
Customer advance auto-application: if customer has advances A, due U is reduced by
min(A, U): Dr Customer Advances min(A,U) instead of AR for that portion.

### 4.2 Customer collection (amount M, allocated Σalloc, advance E)
```
Dr Cash/Bank               M
    Cr Accounts Receivable Σalloc
    Cr Customer Advances   E
```
FIFO allocation to oldest open invoices; allocation rows persisted. Never revenue.

### 4.3 Purchase (net cost N, input tax V, total T = N + V, paid P, due U)
```
Dr Inventory               N
Dr VAT Receivable          V (if recoverable enabled)
    Cr Cash/Bank           P
    Cr Accounts Payable    U
```

### 4.4 Supplier payment (M)
```
Dr Accounts Payable        Σalloc
Dr Supplier Advances       E
    Cr Cash/Bank           M
```

### 4.5 Sales return (refund value R at original sale prices, restock value C₀)
```
Dr Sales Returns           R_net (excl. tax)
Dr VAT Payable             R_tax (if taxed)
    Cr Cash/Bank           refund_paid (if refund)
    Cr Accounts Receivable credit_to_due (if not refunded)
Dr Inventory               C₀ (restocked portion)
    Cr COGS                C₀
```
Damaged portion: no inventory entry (loss remains in COGS); recorded in return items.

### 4.6 Purchase return (value N₀ at original cost, tax V₀)
```
Dr Accounts Payable / Cash N₀ + V₀ (credit received or refund)
    Cr Inventory           N₀ (capped, §3)
    Cr VAT Receivable      V₀ (if recoverable)
(Variances → Dr/Cr 5100 as needed to balance.)
```

### 4.7 Expense (E) / Other income (I)
```
Dr Expense category        E          Dr Cash/Bank  I
    Cr Cash/Bank           E              Cr Other Income  I
```
Loans received: Dr Cash / Cr Loan Payable (2200). Capital: Dr Cash / Cr 3000.
Cash↔bank transfers: Dr Bank / Cr Cash (or reverse) — never income/expense.

### 4.8 Stock adjustment / write-off — see §3.
### 4.9 Opening balances
Customer AR: Dr 1100 / Cr 3900. Supplier AP: Dr 3900 / Cr 2000.
Inventory: Dr 1200 / Cr 3900. Cash: Dr 1000 / Cr 3900. Bank: Dr 1010 / Cr 3900.
### 4.10 Cash closing variance (counted − expected)
Over: Dr Cash / Cr 4950. Short: Dr 6xxx Cash Short expense / Cr Cash.
Finalized sessions are immutable (no edits; new session next day).

## 5. Reports (definitions)
- **Net Sales** = Σ(sales.total − tax) for posted sales in period − Σ sales returns (net).
- **Gross Profit** = Net Sales − COGS (COGS net of returns restock).
- **Operating Profit** = Gross Profit + Other Income − Operating Expenses.
- **Net Profit** = Operating Profit + non-operating income − non-operating expense.
- **Trial Balance**: Σdebits = Σcredits over all posted lines (always, by construction).
- **Balance Sheet**: assets = liabilities + equity + retained earnings (period result).
- **Cashbook**: all journal lines touching 1000/1010 with source references.
- **Customer ledger**: AR subledger lines per customer (opening, sales due, collections,
  returns credit, advance activity) with running balance.
- **Reconciliation** checks (diagnostics, read-only):
  R1 Σ open sale dues == AR balance; R2 Σ open purchase dues == AP balance;
  R3 Σ stock pools == Inventory GL; R4 Σ cash journals == cash session expectation;
  R5 trial balance balanced; R6 movements ↔ pool deltas; R7 payments allocated ≤ paid.

## 6. Tax treatment
Configurable: disabled (default), exclusive, inclusive; rate in basis points (0.01%).
Tax is computed per line on the discounted line base, half-up, then summed. No claim
of Bangladesh statutory VAT compliance; owner must configure per legal advice.

## 7. Worked example (test fixture)
Buy 10 pcs @ ৳50 = ৳500 cash → pool(10, 50000p). Sell 3 @ ৳80, discount ৳10, cash:
line gross 24000p, net 23000p; COGS = round(50000×3/10) = 15000p.
Journal: Dr Cash 23000 / Cr Sales 23000; Dr COGS 15000 / Cr Inventory 15000.
Pool → (7, 35000p). Gross profit = 23000 − 15000 = 8000p (৳80). Return 1 pc restock:
restock value = round(15000×1/3) = 5000p; Dr Sales Returns 7667p (23000/3 rounded),
Cr Cash 7667p; Dr Inventory 5000 / Cr COGS 5000. Pool → (8, 40000p).
