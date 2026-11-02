# Master Feature Checklist — Vybora Business Suite

Status legend: NOT_STARTED · IN_PROGRESS · IMPLEMENTED · TESTED · VERIFIED · BLOCKED.
VERIFIED requires: implementation + DB integration + validation + error handling +
passing automated/documented-manual tests + acceptance criteria + integration tests.
Columns: ID | Requirement | Status | Implementation | Tests | Verified | Notes.
This file is updated at every milestone; it is the release gate register.

## FND — Foundation
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| FND-01 | App startup, composition root, dependency wiring | NOT_STARTED | src/vybora/app.py | — | — | |
| FND-02 | SQLite connection management, WAL, FK, busy timeout, synchronous | NOT_STARTED | src/vybora/data/db.py | — | — | |
| FND-03 | Automatic schema migrations (ordered, transactional, versioned) | NOT_STARTED | src/vybora/data/migrations.py | — | — | |
| FND-04 | Structured logging, no secrets in logs | NOT_STARTED | src/vybora/core/logging.py | — | — | |
| FND-05 | Centralized Bengali error handling (no stack traces to users) | NOT_STARTED | src/vybora/core/errors.py | — | — | |
| FND-06 | Configuration & Windows-safe data paths (data outside install dir) | NOT_STARTED | src/vybora/core/paths.py | — | — | |
| FND-07 | Bengali typography (Noto Sans Bengali, OFL) loaded app-wide | NOT_STARTED | src/vybora/ui/theme.py | — | — | |
| FND-08 | Navigation framework (sidebar + header + stacked pages) | NOT_STARTED | src/vybora/ui/main_window.py | — | — | |
| FND-09 | Light-only design system (colors, spacing, states) | NOT_STARTED | src/vybora/ui/theme.py | — | — | |
| FND-10 | Bengali digit/currency/date formatting utilities | NOT_STARTED | src/vybora/core/formatting.py | — | — | |

## DAT — Database
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| DAT-01 | Normalized schema: core/product/party/sales/purchase/financial/ops tables | NOT_STARTED | src/vybora/data/migrations/0001_initial.sql | — | — | |
| DAT-02 | PK/FK/UNIQUE/NOT NULL/CHECK constraints | NOT_STARTED | 0001_initial.sql | — | — | |
| DAT-03 | Referential integrity enforced (PRAGMA foreign_keys=ON) | NOT_STARTED | data/db.py | — | — | |
| DAT-04 | Atomic multi-table transactions, rollback on failure | NOT_STARTED | services/* | — | — | |
| DAT-05 | Idempotency via unique request_id on posted documents | NOT_STARTED | services/* | — | — | |
| DAT-06 | Transaction-safe invoice/document numbering (sequences) | NOT_STARTED | data/sequences.py | — | — | |
| DAT-07 | Indexed search (products, parties, documents) | NOT_STARTED | 0001_initial.sql | — | — | |
| DAT-08 | Crash recovery (WAL + synchronous FULL), restart tests | NOT_STARTED | data/db.py | — | — | |
| DAT-09 | Integrity & FK diagnostics (integrity_check, foreign_key_check) | NOT_STARTED | data/diagnostics.py | — | — | |
| DAT-10 | Migration failure safety (rollback, no partial schema) | NOT_STARTED | data/migrations.py | — | — | |
| DAT-11 | No artificial product/transaction caps | NOT_STARTED | schema/services | — | — | |
| DAT-12 | Batch/expiry architecture (batches, batch-level stock) | NOT_STARTED | 0001_initial.sql | — | — | |

## ACC — Accounting
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| ACC-01 | Chart of accounts (assets/liabilities/equity/income/COGS/expenses) | NOT_STARTED | domain/accounting.py + seed | — | — | |
| ACC-02 | Journal entries + lines; Σdebit=Σcredit enforced | NOT_STARTED | services/accounting_service.py | — | — | |
| ACC-03 | Posting: cash/credit/partial sales | NOT_STARTED | services/sales_service.py | — | — | |
| ACC-04 | Posting: customer collections (FIFO + advances) | NOT_STARTED | services/payment_service.py | — | — | |
| ACC-05 | Posting: cash/credit/partial purchases | NOT_STARTED | services/purchase_service.py | — | — | |
| ACC-06 | Posting: supplier payments | NOT_STARTED | services/payment_service.py | — | — | |
| ACC-07 | Posting: expenses & other income | NOT_STARTED | services/expense_service.py | — | — | |
| ACC-08 | Posting: sales returns (refund/credit, restock/damaged) | NOT_STARTED | services/return_service.py | — | — | |
| ACC-09 | Posting: purchase returns | NOT_STARTED | services/return_service.py | — | — | |
| ACC-10 | Posting: stock adjustments / write-offs | NOT_STARTED | services/inventory_service.py | — | — | |
| ACC-11 | Posting: opening balances (equity, not revenue) | NOT_STARTED | services/opening_service.py | — | — | |
| ACC-12 | Moving weighted-average COGS (value pool, immutable history) | NOT_STARTED | domain/inventory.py | — | — | |
| ACC-13 | P&L: net sales, gross profit, operating profit, net profit | NOT_STARTED | services/report_service.py | — | — | |
| ACC-14 | Trial balance, general ledger, balance sheet | NOT_STARTED | services/report_service.py | — | — | |
| ACC-15 | Reconciliation suite (sales↔ledger, AR/AP, stock↔GL, cash, trial balance) | NOT_STARTED | services/reconciliation_service.py | — | — | |
| ACC-16 | Cash variance posting on cash closing | NOT_STARTED | services/cash_service.py | — | — | |

## DSH — Dashboard
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| DSH-01 | Today's sales, returns, gross profit, expenses, net cash | NOT_STARTED | services/dashboard_service.py | — | — | |
| DSH-02 | Customer/supplier outstanding, stock value, low-stock count | NOT_STARTED | services/dashboard_service.py | — | — | |
| DSH-03 | Recent transactions list | NOT_STARTED | services/dashboard_service.py | — | — | |
| DSH-04 | Daily sales trend chart (real data) | NOT_STARTED | ui/pages/dashboard.py | — | — | |
| DSH-05 | Monthly comparison, sales vs purchases charts | NOT_STARTED | ui/pages/dashboard.py | — | — | |
| DSH-06 | Expense breakdown, top products, stock alerts | NOT_STARTED | ui/pages/dashboard.py | — | — | |
| DSH-07 | Balanced responsive grid, scrolling, no fake figures | NOT_STARTED | ui/pages/dashboard.py | — | — | |

## PRD — Products
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| PRD-01 | Product fields (name, SKU, barcode, category, brand, unit, prices, min stock, description, image, active, timestamps) | NOT_STARTED | services/product_service.py | — | — | |
| PRD-02 | Add/edit/view/deactivate product | NOT_STARTED | services/product_service.py | — | — | |
| PRD-03 | Search/filter/sort products | NOT_STARTED | data/repositories | — | — | |
| PRD-04 | Duplicate SKU/barcode prevention | NOT_STARTED | services/product_service.py | — | — | |
| PRD-05 | No hard-delete of referenced products | NOT_STARTED | services/product_service.py | — | — | |
| PRD-06 | Product import (CSV) with validation | NOT_STARTED | services/product_import.py | — | — | |
| PRD-07 | Product export (CSV/XLSX) | NOT_STARTED | reporting/* | — | — | |
| PRD-08 | Bulk price updates | NOT_STARTED | services/product_service.py | — | — | |
| PRD-09 | Price history tracking | NOT_STARTED | product_price_history | — | — | |
| PRD-10 | Product UI (list, form, details) | NOT_STARTED | ui/pages/products.py | — | — | |

## INV — Inventory
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| INV-01 | Opening stock with valuation & journal | NOT_STARTED | services/inventory_service.py | — | — | |
| INV-02 | Purchase increases, sale decreases, returns adjust | NOT_STARTED | services/* | — | — | |
| INV-03 | Manual adjustment / damaged / expired write-off | NOT_STARTED | services/inventory_service.py | — | — | |
| INV-04 | Stock movement history (auditable references) | NOT_STARTED | stock_movements | — | — | |
| INV-05 | Low-stock alerts | NOT_STARTED | services/dashboard_service.py | — | — | |
| INV-06 | Stock valuation report (value pool) | NOT_STARTED | services/report_service.py | — | — | |
| INV-07 | Negative-stock policy (configurable, default off) | NOT_STARTED | services/sales_service.py | — | — | |
| INV-08 | Barcode/SKU/name lookup for scanners | NOT_STARTED | services/product_service.py | — | — | |
| INV-09 | Batch-level stock, expiry alerts | NOT_STARTED | services/batch_service.py | — | — | |
| INV-10 | Inventory UI (movements, adjustments, alerts) | NOT_STARTED | ui/pages/inventory.py | — | — | |

## POS — POS & Sales
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| POS-01 | Fast search (name/SKU/barcode), cart, qty/price/discount editing | NOT_STARTED | ui/pages/pos.py | — | — | |
| POS-02 | Line discount, overall discount, auto subtotal/total | NOT_STARTED | domain/sales.py | — | — | |
| POS-03 | Customer selection, payment method, cash tendered/change | NOT_STARTED | ui/pages/pos.py | — | — | |
| POS-04 | Partial payment / credit sale / due calculation | NOT_STARTED | services/sales_service.py | — | — | |
| POS-05 | Pre-posting validation (items, qty, prices, discounts, stock, settings) | NOT_STARTED | domain/sales.py | — | — | |
| POS-06 | Keyboard shortcuts, touch-friendly targets | NOT_STARTED | ui/pages/pos.py | — | — | |
| POS-07 | Unique transaction-safe invoice number | NOT_STARTED | data/sequences.py | — | — | |
| POS-08 | Invoice content (business, customer, lines, totals, paid, due, footer) | NOT_STARTED | reporting/invoice.py | — | — | |
| POS-09 | A4 + thermal 58/80mm layouts, print preview, printer selection | NOT_STARTED | reporting/invoice.py + ui | — | — | |
| POS-10 | PDF export of invoice | NOT_STARTED | reporting/pdf.py | — | — | |
| POS-11 | Reprint history | NOT_STARTED | services/sales_service.py | — | — | |
| POS-12 | Sales history (search/filter/details/reprint/return) | NOT_STARTED | ui/pages/sales_history.py | — | — | |
| POS-13 | Cancellation via controlled reversal (no silent delete) | NOT_STARTED | services/sales_service.py | — | — | |
| POS-14 | Invoice generated from saved data, not UI state | NOT_STARTED | reporting/invoice.py | — | — | |
| POS-15 | Idempotent sale submission | NOT_STARTED | services/sales_service.py | — | — | |
| POS-16 | POS UI complete & functional | NOT_STARTED | ui/pages/pos.py | — | — | |

## CUS — Customers
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| CUS-01 | Customer profile fields + opening balance | NOT_STARTED | services/customer_service.py | — | — | |
| CUS-02 | Create/edit/search/deactivate | NOT_STARTED | services/customer_service.py | — | — | |
| CUS-03 | Credit sales & partial/full collections | NOT_STARTED | services/payment_service.py | — | — | |
| CUS-04 | Payment history, due statement, date statements, ledger | NOT_STARTED | services/report_service.py | — | — | |
| CUS-05 | Balance derived from postings; reconciliation | NOT_STARTED | services/reconciliation_service.py | — | — | |
| CUS-06 | FIFO allocation + advances rules | NOT_STARTED | services/payment_service.py | — | — | |
| CUS-07 | Customer UI | NOT_STARTED | ui/pages/customers.py | — | — | |

## SUP — Suppliers
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| SUP-01 | Supplier profile fields + opening balance | NOT_STARTED | services/supplier_service.py | — | — | |
| SUP-02 | Create/edit/search/deactivate | NOT_STARTED | services/supplier_service.py | — | — | |
| SUP-03 | Purchase/payment history, ledger, statements | NOT_STARTED | services/report_service.py | — | — | |
| SUP-04 | Partial/full payments, FIFO allocation + advances | NOT_STARTED | services/payment_service.py | — | — | |
| SUP-05 | Payable derived from postings; reconciliation | NOT_STARTED | services/reconciliation_service.py | — | — | |
| SUP-06 | Supplier UI | NOT_STARTED | ui/pages/suppliers.py | — | — | |

## PUR — Purchases
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| PUR-01 | Purchase fields (no, supplier, date, items, costs, discount, tax, totals, paid, due, method, ref) | NOT_STARTED | services/purchase_service.py | — | — | |
| PUR-02 | Cash/credit/partial purchases | NOT_STARTED | services/purchase_service.py | — | — | |
| PUR-03 | Post: stock+, valuation, payable, journals, movements | NOT_STARTED | services/purchase_service.py | — | — | |
| PUR-04 | Additional cost allocation & tax treatment | NOT_STARTED | domain/purchases.py | — | — | |
| PUR-05 | Purchase history & details | NOT_STARTED | ui/pages/purchases.py | — | — | |
| PUR-06 | Purchase cancellation via reversal | NOT_STARTED | services/purchase_service.py | — | — | |
| PUR-07 | Idempotent purchase submission | NOT_STARTED | services/purchase_service.py | — | — | |
| PUR-08 | Purchase UI complete | NOT_STARTED | ui/pages/purchases.py | — | — | |

## RTN — Returns
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| RTN-01 | Full/partial/product-specific sales return | NOT_STARTED | services/return_service.py | — | — | |
| RTN-02 | Return qty ≤ eligible; reason required | NOT_STARTED | services/return_service.py | — | — | |
| RTN-03 | Refund or customer credit; restock or damaged | NOT_STARTED | services/return_service.py | — | — | |
| RTN-04 | Return reference + accounting reversal | NOT_STARTED | services/return_service.py | — | — | |
| RTN-05 | Full/partial purchase return, supplier credit/refund | NOT_STARTED | services/return_service.py | — | — | |
| RTN-06 | Purchase return stock deduction + valuation | NOT_STARTED | services/return_service.py | — | — | |
| RTN-07 | Return history UI | NOT_STARTED | ui/pages/returns.py | — | — | |

## EXP — Expenses & income
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| EXP-01 | Expense fields (date, category, amount, account, description, ref, user, ts) | NOT_STARTED | services/expense_service.py | — | — | |
| EXP-02 | Expense categories management | NOT_STARTED | services/expense_service.py | — | — | |
| EXP-03 | Controlled expense correction (reversal + re-post) | NOT_STARTED | services/expense_service.py | — | — | |
| EXP-04 | Receipt attachment (safe local file copy) | NOT_STARTED | services/expense_service.py | — | — | |
| EXP-05 | Other income (separate from sales; loans/capital excluded) | NOT_STARTED | services/expense_service.py | — | — | |
| EXP-06 | Expense/income history & reports | NOT_STARTED | ui/pages/expenses.py | — | — | |
| EXP-07 | Expense/income UI complete | NOT_STARTED | ui/pages/expenses.py | — | — | |

## CSH — Cashbook & closing
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| CSH-01 | Cashbook: all cash movements categorized | NOT_STARTED | services/cash_service.py | — | — | |
| CSH-02 | Opening cash, expected vs counted, variance | NOT_STARTED | services/cash_service.py | — | — | |
| CSH-03 | Daily closing with notes + responsible user | NOT_STARTED | services/cash_service.py | — | — | |
| CSH-04 | Closing history + audit; finalized sessions immutable | NOT_STARTED | services/cash_service.py | — | — | |
| CSH-05 | Cashbook/closing UI | NOT_STARTED | ui/pages/cashbook.py | — | — | |

## RPT — Reporting & exports
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| RPT-01 | Daily/weekly/monthly/custom sales reports | NOT_STARTED | services/report_service.py | — | — | |
| RPT-02 | Purchase report | NOT_STARTED | services/report_service.py | — | — | |
| RPT-03 | Product sales / top-selling reports | NOT_STARTED | services/report_service.py | — | — | |
| RPT-04 | Low-stock / stock movement / valuation reports | NOT_STARTED | services/report_service.py | — | — | |
| RPT-05 | Customer/supplier due reports & ledgers | NOT_STARTED | services/report_service.py | — | — | |
| RPT-06 | Expense / income reports | NOT_STARTED | services/report_service.py | — | — | |
| RPT-07 | Cashbook / daily closing reports | NOT_STARTED | services/report_service.py | — | — | |
| RPT-08 | Sales/purchase return reports | NOT_STARTED | services/report_service.py | — | — | |
| RPT-09 | P&L / general ledger / trial balance / balance sheet | NOT_STARTED | services/report_service.py | — | — | |
| RPT-10 | Transaction history / user activity reports | NOT_STARTED | services/report_service.py | — | — | |
| RPT-11 | Filters: date, product, category, customer, supplier, method, status, user | NOT_STARTED | services/report_service.py | — | — | |
| RPT-12 | PDF export (Bengali-correct, totals, pagination) | NOT_STARTED | reporting/pdf.py | — | — | |
| RPT-13 | CSV export (UTF-8 BOM) | NOT_STARTED | reporting/csv_export.py | — | — | |
| RPT-14 | XLSX export (Bengali, formats, widths) | NOT_STARTED | reporting/excel.py | — | — | |
| RPT-15 | Reports UI with filters & export actions | NOT_STARTED | ui/pages/reports.py | — | — | |

## USR — Users, roles, audit
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| USR-01 | Initial admin setup (no hardcoded credentials) | NOT_STARTED | services/auth_service.py | — | — | |
| USR-02 | Secure login (argon2id), lockout, session mgmt | NOT_STARTED | services/auth_service.py | — | — | |
| USR-03 | Password change, user deactivation | NOT_STARTED | services/auth_service.py | — | — | |
| USR-04 | Roles: owner/admin, manager, cashier, inventory, accountant | NOT_STARTED | services/user_service.py | — | — | |
| USR-05 | Granular permissions enforced in services | NOT_STARTED | security/permissions.py | — | — | |
| USR-06 | Audit logging (login, CRUD, postings, backup, license, permissions) | NOT_STARTED | services/audit_service.py | — | — | |
| USR-07 | Users & permissions UI | NOT_STARTED | ui/pages/users.py | — | — | |
| USR-08 | Login screen & first-run wizard | NOT_STARTED | ui/pages/login.py | — | — | |

## SET — Settings & localization
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| SET-01 | Business info (name, owner, address, phone, email, logo, type, footer) | NOT_STARTED | services/settings_service.py | — | — | |
| SET-02 | Currency/date/digit display preferences | NOT_STARTED | services/settings_service.py | — | — | |
| SET-03 | Tax/VAT configurable (inclusive/exclusive, rate) | NOT_STARTED | services/settings_service.py | — | — | |
| SET-04 | Units (piece, kg, g, litre, ml, packet, box, dozen, carton, metre) | NOT_STARTED | services/settings_service.py | — | — | |
| SET-05 | Negative-stock policy setting | NOT_STARTED | services/settings_service.py | — | — | |
| SET-06 | Settings UI | NOT_STARTED | ui/pages/settings.py | — | — | |

## BKP — Backup & restore
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| BKP-01 | Manual backup (destination choice, details, verify) | NOT_STARTED | services/backup_service.py | — | — | |
| BKP-02 | Automatic backup (daily/weekly, retention, external drive) | NOT_STARTED | services/backup_service.py | — | — | |
| BKP-03 | Backup integrity verification + manifest + SHA-256 | NOT_STARTED | services/backup_service.py | — | — | |
| BKP-04 | Restore: warn (bn), validate, pre-backup, close conns, atomic swap, re-verify | NOT_STARTED | services/backup_service.py | — | — | |
| BKP-05 | Backup history + audit | NOT_STARTED | backup_history | — | — | |
| BKP-06 | Backup/restore UI | NOT_STARTED | ui/pages/backup.py | — | — | |

## LIC — Licensing
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| LIC-01 | Ed25519 signed license format (all fields verified) | NOT_STARTED | licensing/* | — | — | |
| LIC-02 | Privacy-conscious machine fingerprint (multi-source, hashed) | NOT_STARTED | licensing/fingerprint.py | — | — | |
| LIC-03 | Activation request file generation | NOT_STARTED | licensing/activation.py | — | — | |
| LIC-04 | Offline license import & verification (fail-closed) | NOT_STARTED | licensing/activation.py | — | — | |
| LIC-05 | Lifetime validity; no recurring online checks | NOT_STARTED | licensing/* | — | — | |
| LIC-06 | Machine transfer/reissue workflow (owner-side) | NOT_STARTED | tools/LicenseGenerator | — | — | |
| LIC-07 | Generator: admin access, key ceremony, sign, preview, export, history, verify, reissue, revocation record | NOT_STARTED | tools/LicenseGenerator (gitignored until private) | — | — | |
| LIC-08 | Public key only in app; no private key in Git/CI/releases | NOT_STARTED | licensing/verify.py + CI | — | — | |
| LIC-09 | Unprovisioned builds fail closed | NOT_STARTED | licensing/verify.py | — | — | |
| LIC-10 | Activation UI (Bengali) | NOT_STARTED | ui/pages/activation.py | — | — | |
| LIC-11 | License metadata + audit | NOT_STARTED | license_metadata | — | — | |
| LIC-12 | Hardware replacement & key rotation documented | NOT_STARTED | docs/licensing/* | — | — | |

## PRF — Performance & reliability
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| PRF-01 | Indexed fast product/party search | NOT_STARTED | schema + queries | — | — | |
| PRF-02 | Responsive POS posting | NOT_STARTED | services/sales_service.py | — | — | |
| PRF-03 | Benchmarks: 1k/10k/50k/100k products; 100k+ transactions | NOT_STARTED | tests/performance | — | — | |
| PRF-04 | Startup/search/sale/report/backup/restore timing + memory evidence | NOT_STARTED | tests/performance | — | — | |
| PRF-05 | Bengali error messages for lock/storage/corruption/space/migration failures | NOT_STARTED | core/errors.py | — | — | |
| PRF-06 | Background report generation where appropriate | NOT_STARTED | ui/workers.py | — | — | |

## UIX — UI/UX quality
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| UIX-01 | Bengali navigation labels (14 modules) | NOT_STARTED | ui/main_window.py | — | — | |
| UIX-02 | Every screen: overflow/clipping/overlap/alignment checked | NOT_STARTED | ui/* | — | — | |
| UIX-03 | Interaction states (default/hover/focus/disabled/loading/success/error) | NOT_STARTED | ui/theme.py | — | — | |
| UIX-04 | Confirmation dialogs for destructive ops; empty states | NOT_STARTED | ui/widgets/* | — | — | |
| UIX-05 | Window resizing & display-scaling checks | NOT_STARTED | tests/ui | — | — | |
| UIX-06 | No non-functional controls | NOT_STARTED | all UI | — | — | |

## HW — Hardware & printing
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| HW-01 | USB barcode scanner (keyboard emulation) support | NOT_STARTED | ui/pages/pos.py | — | — | |
| HW-02 | Windows printer selection + print preview | NOT_STARTED | reporting/printing.py | — | — | |
| HW-03 | A4 + thermal 58/80mm receipt layouts | NOT_STARTED | reporting/invoice.py | — | — | |
| HW-04 | Touch/mouse/keyboard usability | NOT_STARTED | ui/* | — | — | |
| HW-05 | USB backup drive support (path selection) | NOT_STARTED | ui/pages/backup.py | — | — | |
| HW-06 | Hardware compatibility notes (unverified models documented) | NOT_STARTED | docs/deployment/HARDWARE.md | — | — | |

## TST — Testing & QA
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| TST-01 | Unit tests: money, discount, tax, stock, cost, profit, balances, allocations, numbering, signatures, validation, dates | NOT_STARTED | tests/unit | — | — | |
| TST-02 | Integration: full sales/credit/purchase/return/expense workflows | NOT_STARTED | tests/integration | — | — | |
| TST-03 | DB tests: empty, large, duplicates, invalid refs, rollback, concurrency, migrations, backup/restore, restart | NOT_STARTED | tests/database | — | — | |
| TST-04 | Licensing tests: valid/invalid/tampered/wrong-machine/missing/reissue/offline | NOT_STARTED | tests/licensing | — | — | |
| TST-05 | UI tests: screens, Bengali, forms, keyboard, tables, dialogs, resize | NOT_STARTED | tests/ui | — | — | |
| TST-06 | Regression suite runs on module changes | NOT_STARTED | CI | — | — | |
| TST-07 | Test evidence: results, logs, coverage, known issues, perf, release checklist | NOT_STARTED | docs/testing/evidence | — | — | |
| TST-08 | Security tests: injection, traversal, tamper, privilege, duplicate posting | NOT_STARTED | tests/security | — | — | |

## SEC — Security
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| SEC-01 | Parameterized SQL everywhere | NOT_STARTED | all data access | — | — | |
| SEC-02 | Input validation centralized | NOT_STARTED | core/validation.py | — | — | |
| SEC-03 | argon2id passwords; no plaintext anywhere | NOT_STARTED | security/passwords.py | — | — | |
| SEC-04 | Permission checks in services (least privilege) | NOT_STARTED | security/permissions.py | — | — | |
| SEC-05 | Audit without secrets | NOT_STARTED | services/audit_service.py | — | — | |
| SEC-06 | Safe file import/paths (traversal protection) | NOT_STARTED | core/files.py | — | — | |
| SEC-07 | Backup restore validation (malicious backups rejected) | NOT_STARTED | services/backup_service.py | — | — | |
| SEC-08 | License signature validation (fail-closed) | NOT_STARTED | licensing/verify.py | — | — | |
| SEC-09 | Dependency vulnerability checks in CI | NOT_STARTED | .github/workflows/security-audit.yml | — | — | |
| SEC-10 | No secrets committed (CI scan + gitignore) | NOT_STARTED | scripts/scan_secrets.py + CI | — | — | |

## INS — Installer
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| INS-01 | PyInstaller Windows build (onedir, embedded Python+Qt) | NOT_STARTED | packaging/pyinstaller.spec | — | — | |
| INS-02 | Inno Setup installer (shortcuts, icon, version, silent install) | NOT_STARTED | installer/vybora.iss | — | — | |
| INS-03 | Data dirs outside install dir (ProgramData/local appdata) | NOT_STARTED | core/paths.py | — | — | |
| INS-04 | Upgrade preserves customer data | NOT_STARTED | installer + CI | — | — | |
| INS-05 | Uninstall keeps business data | NOT_STARTED | installer/vybora.iss | — | — | |
| INS-06 | Clean install / upgrade / uninstall tested on Windows CI | NOT_STARTED | .github/workflows/release.yml | — | — | |
| INS-07 | License Generator excluded from customer installer | NOT_STARTED | packaging + CI | — | — | |
| INS-08 | Runtime dependencies included (no system Python needed) | NOT_STARTED | packaging | — | — | |

## CICD — CI/CD
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| CICD-01 | CI: checkout, SDK, restore, format, lint, build, unit+integration, security, results | NOT_STARTED | .github/workflows/ci.yml | — | — | |
| CICD-02 | Windows runners for Windows builds/tests | NOT_STARTED | ci.yml | — | — | |
| CICD-03 | Tag release: verify version, build, test, publish, installer, checksums, metadata, release | NOT_STARTED | .github/workflows/release.yml | — | — | |
| CICD-04 | Least-privilege permissions; pinned actions | NOT_STARTED | workflows | — | — | |
| CICD-05 | SemVer + VERSION + CHANGELOG + release notes | NOT_STARTED | VERSION/CHANGELOG.md | — | — | |
| CICD-06 | Release artifacts: installer EXE, SHA-256, notes, docs | NOT_STARTED | release.yml | — | — | |
| CICD-07 | No signing secrets in release workflow; generator not published | NOT_STARTED | release.yml | — | — | |
| CICD-08 | Failed build → no release | NOT_STARTED | release.yml | — | — | |

## DOC — Documentation
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| DOC-01 | Requirements, architecture, DB, accounting, security, licensing docs | NOT_STARTED | docs/* | — | — | |
| DOC-02 | Bengali user manual (20 topics) | NOT_STARTED | docs/user-manual/ | — | — | |
| DOC-03 | Build/release/deployment instructions | NOT_STARTED | docs/deployment/* | — | — | |
| DOC-04 | Dependency inventory & licenses | NOT_STARTED | docs/deployment/DEPENDENCIES.md | — | — | |
| DOC-05 | Known limitations register | NOT_STARTED | docs/release/KNOWN_LIMITATIONS.md | — | — | |
| DOC-06 | Privacy policy, EULA, third-party notices, support config | NOT_STARTED | docs/legal/* | — | — | |

## BRD — Branding
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| BRD-01 | Name + naming research + limitations | NOT_STARTED | docs/branding/BRAND_IDENTITY.md | — | — | |
| BRD-02 | Logo SVG/PNG + Windows ICO (multi-size) | NOT_STARTED | assets/branding, assets/icons | — | — | |
| BRD-03 | Splash screen | NOT_STARTED | assets/branding | — | — | |
| BRD-04 | Brand colors/typography/iconography guidelines | NOT_STARTED | docs/branding + ui/theme.py | — | — | |
| BRD-05 | Asset license inventory | NOT_STARTED | docs/branding/ASSET_LICENSES.md | — | — | |

## COM — Commercial
| ID | Requirement | Status | Implementation | Tests | Verified | Notes |
|---|---|---|---|---|---|---|
| COM-01 | One-time lifetime license model documented | NOT_STARTED | docs/licensing/* | — | — | |
| COM-02 | Version info shown in app | NOT_STARTED | ui (about) | — | — | |
| COM-03 | Installation & activation instructions (bn) | NOT_STARTED | docs/user-manual | — | — | |
| COM-04 | Troubleshooting & backup guide (bn) | NOT_STARTED | docs/user-manual | — | — | |
| COM-05 | Support contact configuration (no fabricated contacts) | NOT_STARTED | settings | — | — | |
| COM-06 | Transparent lifetime vs optional support distinction | NOT_STARTED | docs/legal/EULA.md | — | — | |

## Release gate summary
- Mandatory items above: **237** (count maintained at each milestone).
- VERIFIED: 0 · TESTED: 0 · IMPLEMENTED: 0 · IN_PROGRESS: 0 · BLOCKED: 0 · NOT_STARTED: 237.
- **No production release until all mandatory items are VERIFIED or explicitly
  re-scoped by the owner in writing.** Hardware-dependent items will carry documented
  owner-run verification evidence before release.
