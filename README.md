# Vybora Business Suite — ভাইবোরা বিজনেস স্যুট

Offline-first Bengali business management & POS desktop software for Windows 10/11
(64-bit), built for Bangladeshi retail, wholesale and small/medium businesses.
One-time payment · lifetime license · no internet required after activation.

> **Status: active development (0.1.0-dev).** No production release yet.
> See `PROJECT_STATUS.md` and `docs/requirements/FEATURE_CHECKLIST.md` for the
> honest, traceable state of every mandatory feature.

## What it will do
POS & invoicing · products & inventory (weighted-average costing) · purchases ·
customers & suppliers with due management · sales/purchase returns · expenses &
other income · cashbook & daily closing · double-entry accounting (ledger, trial
balance, P&L, balance sheet) · 26 report types with PDF/CSV/Excel export ·
roles & permissions · audit trail · automatic/manual backup & safe restore ·
offline Ed25519 lifetime licensing · professional Windows installer.

## Technology
Python 3.11+ · PySide6 (Qt 6) · SQLite · argon2id · Ed25519 · openpyxl ·
PyInstaller + Inno Setup (Windows, via GitHub Actions). See `DECISION_LOG.md`.

## Repository guide
- `PROJECT_STATUS.md`, `IMPLEMENTATION_ROADMAP.md`, `BLOCKERS.md`, `DECISION_LOG.md`
- `docs/requirements/FEATURE_CHECKLIST.md` — master traceability (237 items)
- `docs/` — architecture, database, accounting, licensing, security, UI, testing, release
- `src/vybora/` — application source (layered: ui → services → domain/data → core)
- `tests/` — unit, integration, database, licensing, UI, security, performance
- `tools/LicenseGenerator/` — owner-only (kept out of public Git until repo is private)
- `.github/workflows/` — CI and tag-based release pipeline

## Development
```bash
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest                                         # full suite
ruff check src tests                           # lint
```
On the Linux sandbox, offscreen Qt tests use dev-only stub libs (`.sandbox-libs/`,
gitignored, never shipped). Windows builds/tests run on GitHub Actions.

## Security
Never commit secrets, private signing keys, customer licenses or real business data.
The app embeds only a public verification key. See `SECURITY.md` and
`docs/licensing/KEY_CEREMONY.md`.

## License
Proprietary commercial software (see `LICENSE` / EULA). Bundled font: Noto Sans
Bengali, SIL OFL 1.1. Third-party notices: `docs/legal/THIRD_PARTY_NOTICES.md`.
