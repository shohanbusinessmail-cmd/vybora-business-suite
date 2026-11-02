# Architecture — Vybora Business Suite

## 1. Stack (ADR-001)
- Python 3.11+ (3.12 on CI), PySide6-Essentials 6.x (Qt 6, LGPL-3.0), SQLite (stdlib).
- argon2-cffi (argon2id), cryptography (Ed25519), openpyxl (XLSX), pytest/pytest-qt.
- Packaging: PyInstaller (onedir, win-x64) + Inno Setup 6 on `windows-latest`.
- No network calls at runtime. No telemetry. All data local.

## 2. Layering (strict dependency direction)
```
ui  →  services  →  domain + data  →  core
         │              │
         ├─ security    ├─ reporting (reads data, renders via Qt/openpyxl)
         └─ licensing   └─ infrastructure (files, backup, printing)
```
- **ui/** (PySide6): windows, pages, dialogs, widgets, theme, workers. Never touches
  SQL or financial rules directly; calls services; renders results.
- **services/** (application layer): use-cases, orchestration, transactions,
  permission checks, audit writes, idempotency. One service per bounded area.
- **domain/** (pure logic, no I/O): money, quantities, sales/purchase calculations,
  inventory costing, accounting posting rules, allocation algorithms, validation.
  Fully unit-testable without a database.
- **data/**: connection factory (WAL, FK, busy_timeout, synchronous=FULL), migration
  runner, repositories (parameterized SQL only), sequences, diagnostics.
- **core/**: errors (Bengali messages), formatting (bn digits/currency/dates),
  paths (Windows-safe), logging (redacted), validation helpers, file safety.
- **security/**: password hashing, permission model, session context.
- **licensing/**: fingerprint, request generation, license verification (public key
  only), activation state. Private signing lives ONLY in tools/LicenseGenerator.
- **reporting/**: report models → PDF (QTextDocument/QPdfWriter), XLSX (openpyxl),
  CSV (utf-8-sig), invoice layouts (A4/58mm/80mm), printing (QPrinter).

## 3. Transaction & posting pipeline
Every posting use-case follows one pattern:
```
with db.transaction():            # single SQLite write transaction
    check_permission(ctx)
    check_idempotency(request_id) # UNIQUE; duplicate → return original
    validate(domain rules)        # raises ValidationError (Bengali)
    allocate_document_number()    # UPDATE sequences ... RETURNING
    write business rows           # sale/purchase/payment/... + lines
    apply_stock(value_pool)       # movements + pool update (if applicable)
    post_journal(entry)           # balanced; enforced before commit
    write_audit_log()
```
Any exception rolls back everything (business rows, stock, journal, audit, number).
Journals are never posted without their source document and vice versa.

## 4. Concurrency model
- Single process, one writer connection guarded by a threading.RLock; UI runs
  long tasks in QThreadPool workers with their own short-lived connections.
- WAL allows concurrent readers; busy_timeout=5000ms; synchronous=FULL for durability.
- All multi-statement writes inside explicit transactions; no autocommit multi-step.

## 5. Error handling
- DomainError/ValidationError/PermissionError/NotFoundError → Bengali user message,
  no stack trace. Unexpected exceptions → generic Bengali message + redacted log entry
  with correlation id. DB locked/disk-full/corrupt mapped to specific Bengali messages.

## 6. Composition root
`app.py` builds: paths → logging → db (migrate) → services → license gate → main window.
Services receive a `SessionFactory` + `SettingsService`; no global singletons except
the Qt application object.

## 7. UI architecture
- QMainWindow: fixed sidebar (14 Bengali modules), header (business name, user, date),
  QStackedWidget pages. Pages are lazily constructed. Dialogs are modal, centered on
  parent. QThreadPool for reports/backups. Light theme via a single QSS stylesheet.
- POS page is keyboard-first: F2 search, Enter add, F4 qty, F9 payment, Esc clear.
- All tables are QTableView over QAbstractTableModel (virtualized for large data).

## 8. Reporting architecture
Report = (metadata, columns, rows, totals) produced by report_service from SQL.
Renderers are pure functions: to_pdf (Qt, embedded Noto Sans Bengali), to_xlsx
(openpyxl, styled), to_csv (utf-8-sig). Invoices render from persisted sale rows only.

## 9. Security architecture
See SECURITY_ARCHITECTURE.md. Summary: argon2id, service-layer RBAC, audit trail,
parameterized SQL, path validation, fail-closed licensing, secret-free logs.

## 10. Licensing architecture
See LICENSING_SPEC.md. Summary: Ed25519 signed canonical JSON, machine fingerprint,
offline request/import flow, public key only in app, owner-only generator.

## 11. Testing architecture
See TESTING_STRATEGY.md. Domain = pure unit tests; services = SQLite integration
tests (temp DBs); UI = pytest-qt offscreen; performance = generated datasets;
Windows-specific = GitHub Actions windows-latest.

## 12. Directory map
```
src/vybora/{core,domain,data,services,security,licensing,reporting,ui,i18n}
tools/LicenseGenerator/        # owner-only (gitignored while repo is public)
tests/{unit,integration,database,licensing,ui,security,performance}
packaging/  installer/  scripts/  .github/workflows/  docs/  assets/
```
