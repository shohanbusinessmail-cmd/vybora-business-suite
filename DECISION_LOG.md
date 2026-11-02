# Decision Log — Vybora Business Suite

Format: ADR-nnn · date · status · decision · rationale · consequences.

---

## ADR-001 — Technology stack: Python 3.11+ / PySide6 (Qt 6) / SQLite
Date: 2026-11-02 · Status: ACCEPTED

**Decision.** Build the desktop application in Python 3.11+ with PySide6 (Qt 6, LGPL),
SQLite via the Python standard library, and package for Windows with PyInstaller +
Inno Setup on GitHub Actions `windows-latest` runners.

**Evaluated alternatives.**
| Option | Verdict | Reason |
|---|---|---|
| C#/.NET 8 + WPF | Rejected here | No .NET SDK in sandbox; NuGet unreachable; cannot develop or run any test locally. Suggested by owner but explicitly non-mandatory. |
| Electron + TS | Rejected here | Electron binaries download from GitHub release assets, which are network-blocked in this sandbox; cannot run the app locally. |
| Tauri (Rust) | Rejected here | No Rust toolchain; crates.io unreachable. |
| Python + PySide6 | **Selected** | All dependencies from PyPI (reachable); Qt gives best-in-class Bengali shaping (HarfBuzz), native widgets, QPrinter/QPdfWriter for Bengali-correct PDF/printing; full local testability (offscreen); mature Windows packaging. |

**Rationale.** The environment can actually build, run and test this stack end-to-end
today, which the correctness-first mandate requires. Qt is proven for complex-script
UIs; SQLite is the standard embedded database; Python `decimal`/integer arithmetic
gives exact money handling.

**Consequences.** Larger installer than a native C# app (~150–250 MB with Qt); Python
source is extractable from PyInstaller bundles (offline licensing limits documented in
LICENSING_SPEC.md — no anti-tamper guarantees are made); LGPL compliance requires
dynamic linking of Qt (PyInstaller onedir keeps Qt DLLs replaceable) and inclusion of
license notices. Runtime: Python 3.11/3.12 embedded via PyInstaller (no system Python
needed on customer machines).

## ADR-002 — Product name: Vybora Business Suite (ভাইবোরা বিজনেস স্যুট)
Date: 2026-11-02 · Status: ACCEPTED

**Decision.** Adopt **Vybora** as the product brand, matching the owner-created
repository `vybora-business-suite`. Bengali display name: **ভাইবোরা বিজনেস স্যুট**.
Pronunciation guide: vy-BOR-ah.

**Research.** Web search (2026-11-02) found small unrelated projects using "VYBORA"
(an entertainment-discovery demo and a social-app demo on GitHub). No established
business-management/POS software brand or obvious trademark conflict was found in the
searched results. Domain availability was not exhaustively checked. **This is not
trademark clearance**; the owner retains final legal responsibility (see
BRAND_IDENTITY.md). The name is short, distinctive, pronounceable in Bengali and
English, and suitable for future expansion beyond POS.

## ADR-003 — Money representation: integer poisha; quantities: integer milli-units
Date: 2026-11-02 · Status: ACCEPTED

**Decision.** All monetary amounts are stored and computed as **integer poisha**
(1 BDT = 100 poisha). Quantities are stored as **integer milli-units** (×1000),
supporting fractional kg/litre/metre without binary floating point. Domain code uses
`decimal.Decimal` only at boundaries (parsing/display); core arithmetic is integer.
Rounding: **round-half-up** to the nearest poisha, applied once per line/entry at
defined points; no floating point anywhere in financial paths.

**Consequences.** Exact sums; no float drift; display layer converts poisha→BDT with
configurable Bengali/international digits. Unit-cost display may show more precision
than stored; stock valuation uses the value-pool method (ADR-004).

## ADR-004 — Inventory costing: moving weighted average (value-pool method)
Date: 2026-11-02 · Status: ACCEPTED

**Decision.** Perpetual inventory with **moving weighted average** cost. Each product
keeps `stock_qty` (milli-units) and `stock_value` (poisha) as the authoritative pool.
COGS for a sale line = `round_half_up(stock_value * qty / stock_qty)` computed at sale
time; the pool is reduced by exactly that amount, so `remaining_value + ΣCOGS =
original_value` exactly (no rounding drift). Purchase returns remove value at original
purchase cost (capped at pool, variance to adjustment account). Sales returns restore
value at the **original recorded COGS** of the sold line. Historical sale costs are
never rewritten when purchase prices change.

**Consequences.** Simple, auditable, drift-free; matches typical BD retail practice.
FIFO rejected (more complex, no practical benefit for target users). Documented in
ACCOUNTING_SPEC.md.

## ADR-005 — Accounting: full double-entry with perpetual inventory
Date: 2026-11-02 · Status: ACCEPTED

**Decision.** Every financial event posts a balanced journal entry (Σdebit = Σcredit,
enforced in the posting service inside the same DB transaction as the business event).
Chart of accounts, general ledger, trial balance, P&L and balance sheet derive from
journals. Business documents (sales, purchases, payments, expenses, returns,
adjustments, opening balances, cash variance) are the source documents; journals
reference them. Customer/supplier balances are derived from subledger postings, not
independently editable fields.

## ADR-006 — Repository security under public visibility
Date: 2026-11-02 · Status: ACCEPTED (owner action pending)

**Decision.** The repository is public and the token cannot change visibility or
create a private repo (verified 403s). Therefore: (a) never commit secrets, private
keys, customer licenses or real data (gitignore + CI scan); (b) keep the owner-only
License Generator source in gitignored `tools/LicenseGenerator/` (persisted in the
Arena workspace) until the repo is private; (c) ship only the public verification key
in the app; (d) CI release workflow receives no signing secrets. **Owner action:**
make the repository private to enable committing/building the generator in Git.

## ADR-007 — License scheme: Ed25519-signed JSON licenses, offline activation
Date: 2026-11-02 · Status: ACCEPTED

**Decision.** Lifetime licenses are Ed25519-signed canonical JSON documents bound to a
privacy-preserving machine fingerprint (SHA-256 of normalized stable hardware IDs).
The app verifies with an embedded public key; the private key exists only on the
owner's offline machine, generated by the License Generator at first run (never in
Git/CI/releases). Production public key is provisioned by the owner via a documented
key ceremony before the first commercial release; until then release builds are
"unprovisioned" and reject activation (fail-closed). Tests use ephemeral keys.

## ADR-008 — Single-branch development on Arena branch
Date: 2026-11-02 · Status: ACCEPTED

**Decision.** All commits go to `arena/08f8f729-vybora-business-suite`. Planning and
implementation milestones are committed and pushed as they complete. Production
release tags are created only after Phase 10/11 acceptance gates pass.

## ADR-009 — Bengali-only customer UI, light theme only
Date: 2026-11-02 · Status: ACCEPTED

**Decision.** All customer-facing strings are centralized in `vybora/i18n/bn.py`.
Light theme only (no dark mode, no theme switching). Noto Sans Bengali (OFL) bundled;
Bengali/international digit display is a preference and never changes stored values.

## ADR-010 — Backup: SQLite online backup API + integrity verification
Date: 2026-11-02 · Status: ACCEPTED

**Decision.** Backups use `sqlite3.Connection.backup()` (consistent snapshot of a live
WAL database), followed by `PRAGMA integrity_check` and foreign-key check on the
backup, plus a JSON manifest (app version, schema version, SHA-256, timestamp).
Restore validates manifest + integrity, takes a pre-restore safety backup, closes all
connections, swaps files atomically, reopens and re-verifies. Automatic backups run on
a QTimer with configurable daily/weekly schedule and retention.

## ADR-011 — Sandbox Qt workaround is dev-only
Date: 2026-11-02 · Status: ACCEPTED

**Decision.** The Linux sandbox lacks libGL/libEGL/libdbus/libxkbcommon and apt is
blocked. Dev-only stub libraries in `.sandbox-libs/` (gitignored) allow offscreen Qt
testing. They are never packaged, never shipped, and never used on Windows. CI on
Windows uses the real Qt/system libraries.

## ADR-012 — Idempotency and numbering
Date: 2026-11-02 · Status: ACCEPTED

**Decision.** Sales, purchases, payments, returns, expenses and adjustments carry a
client-generated UUID `request_id` with a UNIQUE constraint; duplicate submissions
return the original result instead of double-posting. Document numbers come from a
`sequences` table updated with `UPDATE ... RETURNING` inside the posting transaction
(no gaps from failed transactions, no duplicates under concurrency).

## ADR-013 — Returns and reversals: no hard deletes of posted documents
Date: 2026-11-02 · Status: ACCEPTED

**Decision.** Posted documents are never deleted. Cancellation is a controlled
reversal that creates offsetting stock movements and journals referencing the
original. Returns reference original lines and enforce returned ≤ sold/purchased.

## ADR-014 — Payment allocation: FIFO with advance accounts
Date: 2026-11-02 · Status: ACCEPTED

**Decision.** Customer collections allocate FIFO to the oldest outstanding invoices;
excess goes to Customer Advances (liability) and is auto-applied to the next credit
sale's due. Supplier payments allocate FIFO to oldest unpaid purchases; excess goes to
Supplier Advances (asset). Allocation rows are persisted for audit. Rules documented
in ACCOUNTING_SPEC.md; both allocation behaviors are covered by tests.

## ADR-015 — Versioning and release gating
Date: 2026-11-02 · Status: ACCEPTED

**Decision.** Semantic versioning; `VERSION` file is the single source of truth,
checked against the tag in CI. Releases are tag-driven (`vX.Y.Z`), built on
`windows-latest`, and gated on the full test suite + installer build. No release is
published if any gate fails. Current version: **0.1.0-dev** (no production release
yet).
