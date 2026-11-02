# Testing Strategy — Vybora Business Suite

## 1. Pyramid
- **Unit (domain)**: pure functions — money rounding, discounts, tax modes, cart math,
  value-pool costing, allocation FIFO, journal balance validation, numbering, license
  canonicalization/signature verification, fingerprint normalization, date ranges,
  formatting (bn digits). No DB, no Qt. Fast, exhaustive edge cases.
- **Integration (services + SQLite)**: temp DB per test; full workflows:
  opening → purchase → sale (cash/credit/partial) → collection → return → expense →
  cash close → reports; assert stock pools, movements, journals, trial balance,
  subledgers, idempotency, rollback on injected failure, permission denials, audit rows.
- **Database**: constraints (duplicates, invalid FK, CHECKs), migration up/failure,
  WAL restart recovery, concurrent readers + serialized writer, backup/restore
  integrity, large dataset smoke (10k products).
- **Licensing**: valid/invalid/tampered/wrong-machine/missing/unprovisioned/reissue/
  offline startup (socket blocked in test).
- **UI (pytest-qt, offscreen)**: every page/dialog constructs; Bengali strings present;
  forms validate; keyboard shortcuts; table models; resize; no English leakage;
  screenshots as evidence.
- **Security**: SQL injection attempts on search fields; path traversal on import/
  restore; privilege escalation attempts; duplicate posting; malicious backup rejection.
- **Performance**: generated datasets (1k/10k/50k/100k products; 100k sales) — measure
  search latency, sale posting, report queries, backup/restore; record hardware +
  results in docs/testing/evidence/PERFORMANCE.md (never fabricated).

## 2. Evidence
- CI uploads junit XML + coverage (pytest --junitxml, coverage) as artifacts.
- Local runs recorded in docs/testing/evidence/ with date, command, result summary.
- Known-issue register: docs/testing/KNOWN_ISSUES.md.
- Windows-only checks: docs/testing/WINDOWS_VERIFICATION.md (owner-run checklist with
  sign-off fields; CI automates what it can: silent install, launch, uninstall).

## 3. Regression policy
Any change to domain/data/services triggers full unit+integration suite locally and in
CI. Financial/stock changes additionally run the reconciliation suite. UI changes run
UI suite. Release requires green full suite on windows-latest + ubuntu (logic).

## 4. Definition of done (per feature)
Implementation + validation + error handling + DB integration + unit/integration tests
passing + audit + permission checks + Bengali UI (if applicable) + checklist updated.
