# Requirements Specification — Vybora Business Suite

Source of truth: the owner's Ultimate Master Prompt (2026-11-02). Every mandatory
requirement is decomposed into traceable IDs below and tracked in
`FEATURE_CHECKLIST.md`. Statuses: NOT_STARTED / IN_PROGRESS / IMPLEMENTED / TESTED /
VERIFIED / BLOCKED. A requirement is VERIFIED only with implementation + integration +
validation + error handling + passing tests + satisfied acceptance criteria.

## 1. Product definition

Offline-first Bengali business management & POS desktop software for Windows 10/11
(64-bit), targeting Bangladeshi grocery stores, retail, supermarkets, wholesale,
electronics, clothing, cosmetics, stationery and (where legally appropriate)
pharmacies. One-time payment, lifetime license. No cloud dependency, no telemetry, no
subscription APIs. Currency: BDT (৳). UI language: Bengali. Light mode only.

## 2. Requirement groups (IDs used in FEATURE_CHECKLIST.md)

| Prefix | Area | Master prompt part |
|---|---|---|
| FND | Foundation (startup, DI, config, logging, errors, migrations, navigation) | 4, 7, 31-P3 |
| DAT | Database integrity & operations | 7 |
| ACC | Accounting engine (double-entry, costing, P&L, reconciliation) | 8 |
| DSH | Dashboard | 9 |
| PRD | Product management | 10.1–10.2 |
| INV | Inventory & stock | 10.3–10.4 |
| POS | POS & sales | 11 |
| CUS | Customers & dues | 12 |
| SUP | Suppliers | 13 |
| PUR | Purchases | 14 |
| RTN | Sales & purchase returns | 15 |
| EXP | Expenses & other income | 16 |
| CSH | Cashbook & cash closing | 17 |
| RPT | Reporting & exports | 18 |
| USR | Users, roles, permissions, audit | 19 |
| SET | Business settings & localization | 20 |
| BKP | Backup & restore | 21 |
| LIC | Offline licensing & generator | 22 |
| PRF | Performance & reliability | 23 |
| UIX | UI/UX quality | 24 |
| HW | Hardware & printing | 25 |
| TST | Testing & QA evidence | 26 |
| SEC | Security | 27 |
| INS | Windows installer | 28 |
| CICD | GitHub Actions CI/CD | 29 |
| DOC | Documentation | 30 |
| BRD | Branding & assets | 3 |
| COM | Commercial distribution | 36 |

## 3. Business rules (normative)

### 3.1 Money & quantities
- BR-M1: Money stored as integer poisha (1 BDT = 100 poisha); no binary floats in any
  financial path. Rounding: half-up to poisha at defined points, once per line.
- BR-M2: Quantities stored as integer milli-units (×1000); fractional units allowed
  only where the product unit permits (kg, g, litre, ml, metre); piece-like units are
  whole-only.
- BR-M3: Display preferences (Bengali digits, separators, precision, currency
  placement) never alter stored values.

### 3.2 Sales
- BR-S1: Sale line total = round(qty × unit_price) − line_discount; sale subtotal =
  Σ line totals; overall discount applied after subtotal; tax (if enabled) computed per
  configured mode (exclusive/inclusive) and rate; final total = subtotal − overall
  discount + tax (exclusive) or extracted tax (inclusive).
- BR-S2: paid + due = final total; paid ≥ 0; due ≥ 0; change = cash_tendered − cash
  portion due (never negative). Overpayment beyond total is rejected at POS (collections
  handle advances separately).
- BR-S3: Stock checked per line at posting time inside the transaction; negative stock
  only if the business policy explicitly allows it (default: forbidden).
- BR-S4: Credit/partial sales require a registered customer. Walk-in cash sales may use
  the implicit walk-in customer.
- BR-S5: Invoice numbers are unique, sequential per series, allocated inside the
  posting transaction.
- BR-S6: Duplicate `request_id` returns the original sale (idempotency).

### 3.3 Purchases
- BR-P1: Purchase increases stock qty and value at net landed cost (incl. allocated
  additional cost, excl. recoverable tax if configured); supplier payable = total − paid.
- BR-P2: Supplier payments reduce payable, never create purchases or revenue.

### 3.4 Returns
- BR-R1: Returned qty ≤ original qty − already returned (per line).
- BR-R2: Sales return restocks at original recorded COGS; damaged returns do not
  restock; refund reduces cash or customer due; contra-revenue account used.
- BR-R3: Purchase return removes stock at original purchase cost (capped at current
  pool value; variance to inventory adjustment); reduces payable or creates refund.

### 3.5 Payments & dues
- BR-C1: Collections allocate FIFO to oldest open invoices; excess → Customer Advances;
  advances auto-apply to next credit sale due. Collections are never revenue.
- BR-C2: Supplier payments allocate FIFO to oldest unpaid purchases; excess → Supplier
  Advances.
- BR-C3: Opening balances post through Opening Balance Equity, never through revenue.

### 3.6 Accounting
- BR-A1: Every posted journal: Σdebits = Σcredits (enforced in-transaction).
- BR-A2: COGS at moving weighted average via value pool (ADR-004); historical costs
  immutable.
- BR-A3: Net Sales = Gross Sales − Discounts − Sales Returns; Gross Profit = Net Sales −
  COGS; Operating Profit = Gross Profit + Other Income − Operating Expenses; Net Profit
  further adjusts non-operating items. Cash received ≠ revenue.
- BR-A4: Loans/capital are financing/equity, never income. Transfers between cash/bank
  are not income/expense.

### 3.7 Inventory
- BR-I1: Every stock change has a movement row with reason + source document + user.
- BR-I2: Referenced products are deactivated, never hard-deleted.
- BR-I3: Stock adjustments require permission and post accounting entries.

### 3.8 Security
- BR-SEC1: Passwords hashed with argon2id; never stored/logged in plaintext.
- BR-SEC2: Permission checks enforced in the service layer (UI hiding is cosmetic).
- BR-SEC3: Audit log records actor, time, action, entity, before/after (no secrets).
- BR-SEC4: License verification is offline, signature-first, fail-closed.

### 3.9 Data safety
- BR-D1: Critical operations are atomic (single SQLite transaction).
- BR-D2: Backups via SQLite online backup API + integrity verification; restore is
  validated, confirmed, pre-backed-up and atomic.
- BR-D3: No hard delete of posted financial documents; reversal only.

## 4. Acceptance criteria

Per-feature acceptance criteria are embedded in FEATURE_CHECKLIST.md rows and the
final gate in `docs/requirements/ACCEPTANCE_CRITERIA.md` (mirrors master prompt Part 35).

## 5. Ambiguities resolved by engineering decision (owner may override)

| Ambiguity | Resolution |
|---|---|
| Multi-branch support | Single business/location in v1; schema keeps `branch_id` nullable for future multi-location; no transfer UI until multi-location ships. Documented limitation. |
| Pharmacy regulatory compliance | Batch/expiry architecture provided; no claim of statutory pharmacy/VAT compliance (owner must validate with authorities). |
| VAT statutory rates | Configurable; no hardcoded statutory claim. |
| "Unlimited" storage | No artificial caps; practical limits documented (SQLite/hardware). |
| Trademark/domain clearance | Research done; legal clearance remains owner responsibility. |
| Support contacts | Configurable placeholders, never fabricated. |
