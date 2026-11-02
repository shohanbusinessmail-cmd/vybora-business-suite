# Implementation Roadmap — Vybora Business Suite

Phases follow the master prompt Part 31. Gates must pass before advancing.
Status key: ✅ done · 🔄 in progress · ⬜ not started.

## PHASE 0 — Repository & environment discovery ✅
Audit: docs/repository/AUDIT.md. Stack verified working (Qt offscreen + Bengali PDF,
argon2, Ed25519, SQLite WAL/backup, openpyxl). Blockers: BLK-001/002/003/006.

## PHASE 1 — Requirements ✅
REQUIREMENTS.md, FEATURE_CHECKLIST.md (237 traceable items), ACCEPTANCE_CRITERIA.md,
RISK_REGISTER.md.

## PHASE 2 — Architecture & design ✅
ARCHITECTURE.md, DATABASE_DESIGN.md, ACCOUNTING_SPEC.md, LICENSING_SPEC.md,
SECURITY_ARCHITECTURE.md, UI_DESIGN_SPEC.md, TESTING_STRATEGY.md, RELEASE_STRATEGY.md,
DECISION_LOG.md (ADR-001…015).

## PHASE 3 — Foundation 🔄
Solution structure, startup/DI, DB connection + migrations, logging, errors, config,
paths, Bengali typography, navigation, design system, formatting.
Gate: app starts offscreen, DB initializes, foundation tests pass.

## PHASE 4 — Core business modules ⬜
Settings → auth/users/roles/permissions → categories/units/brands → products →
inventory → suppliers → customers → accounting foundation (COA, journals).
Gate: core entity rules + accounting invariants pass tests.

## PHASE 5 — Operational modules ⬜
POS/sales/invoices → payments/dues → purchases → supplier payments → sales returns →
purchase returns → expenses/other income → cashbook → cash closing.
Gate: all end-to-end workflows pass integration tests.

## PHASE 6 — Financial reporting ⬜
Ledgers, trial balance, P&L, balance sheet, sales/purchase/stock/due/expense/cash/
return/activity reports + PDF/CSV/XLSX exports.
Gate: reports reconcile with authoritative records.

## PHASE 7 — Backup, security, licensing ⬜
Auto/manual backup, restore, integrity, audit completion, license verification +
activation + fingerprint, owner-only generator, key ceremony docs.
Gate: backup/restore + offline activation tests pass.

## PHASE 8 — UI/UX completion ⬜
All screens/dialogs/forms/notifications/empty/loading/error states, keyboard,
printing interfaces, Bengali audit, resize/scaling checks.
Gate: UI suite passes; no non-functional controls.

## PHASE 9 — Full QA & optimization ⬜
Full suites, reconciliation, stress/perf benchmarks, security review, offline test.
Gate: no known critical/high defects; evidence recorded.

## PHASE 10 — Installer & release prep ⬜
PyInstaller + Inno Setup, CI release workflow, clean install/upgrade/uninstall on
Windows CI, versioning, docs, EULA/notices.
Gate: installer builds + CI install/launch/uninstall smoke passes.

## PHASE 11 — Final production release ⬜
Final review/tests/build, checksums, tag v1.0.0, GitHub Release with installer.
Gate: all Part 35 acceptance items satisfied; release published & verified.

## Current focus
Phase 3 foundation implementation + tests, then Phase 4 core modules.
