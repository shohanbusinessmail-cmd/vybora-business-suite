# Phase 0 — Repository & Environment Audit

Date: 2026-11-02 · Auditor: autonomous engineering agent (Arena Agent Mode)

## 1. Repository

| Item | Finding |
|---|---|
| Repository | `shohanbusinessmail-cmd/vybora-business-suite` |
| Owner | `shohanbusinessmail-cmd` (authenticated identity confirmed via `gh auth status`) |
| Initial state | Effectively empty: single commit `7945997 Initial commit`, only `README.md` |
| Default branch | `main` |
| Working branch | `arena/08f8f729-vybora-business-suite` (fixed by Arena; all work happens here) |
| Visibility | **Public** (see security decision below) |
| Effective permission | `ADMIN` (`viewerCanAdminister: true`) |
| Token type | Fine-grained GitHub App integration token |
| Actions runs at audit | 0 (no workflows yet) |

### Token capability probe (actual API results)

| Operation | Result |
|---|---|
| Read repo metadata / contents / branches | ✅ allowed |
| Read Actions runs list | ✅ allowed |
| `GET /actions/permissions` | ❌ 403 (token scope) |
| `PATCH /repos/...` (change visibility) | ❌ 403 — **cannot make repo private** |
| `POST /user/repos` (create private repo) | ❌ 403 — **cannot create a separate private repo** |
| Push commits | ✅ verified (planning milestone push) |
| Push `.github/workflows` | see BLOCKERS.md — verified at first CI push |

## 2. Security consequence of public visibility

The master specification prefers a private repository during development because the
project contains a proprietary License Generator. The token cannot change visibility
and cannot create a second private repository.

**Mitigation applied (documented in DECISION_LOG.md, ADR-006):**

1. No private signing key, customer license, credential, or real business data is ever
   committed (enforced by `.gitignore` + CI secret scan).
2. The owner-only License Generator source is kept **out of public Git** in a
   gitignored workspace directory (`tools/LicenseGenerator/`) until the owner either
   makes this repository private or provides a private repository for it.
3. The main application embeds only a **public** verification key.
4. Owner action requested: make the repository private (GitHub → Settings → General →
   Danger Zone → Change visibility), after which the generator can be committed and
   built by a restricted workflow.

## 3. Development environment (sandbox)

| Item | Finding |
|---|---|
| OS | Debian 12 (bookworm), Linux x86_64 — **not Windows** |
| CPU / RAM / Disk | 2 vCPU / 3.8 GiB / ~20 GiB free |
| Python | 3.11.2 (+ project venv at `.venv/`) |
| Node.js | 22.22.3 (has experimental `node:sqlite`) |
| .NET SDK | not installed; NuGet unreachable → .NET/WPF not developable here |
| Rust / crates.io | not installed; crates.io unreachable → Tauri not developable here |
| Wine / NSIS / Inno Setup | not installed locally |
| Compiler | gcc 12.2 available |
| Network allowlist | github.com, codeload.github.com, api.github.com, registry.npmjs.org, pypi.org, files.pythonhosted.org |
| GitHub release asset downloads | **blocked** (release-assets.githubusercontent.com unreachable) → Electron binaries cannot be fetched locally |
| apt / Debian mirrors | blocked → system packages cannot be installed |

### Verified working capabilities (actual test runs)

- PyPI installs: `PySide6-Essentials 6.12.0`, `argon2-cffi 25.1.0`, `cryptography 50.0.2`,
  `openpyxl 3.1.5`, `pytest 9.2.0`, `pytest-qt 4.5.0`, `ruff 0.17.3`.
- Qt 6.12 offscreen rendering works after providing dev-only stub shared libraries for
  `libGL/libEGL/libdbus-1/libxkbcommon` (missing system libs; apt blocked). Stubs live in
  `.sandbox-libs/` (gitignored, **never shipped**, Windows uses real system libraries).
- Bengali font `Noto Sans Bengali` (OFL) downloaded from `google/fonts` via GitHub API,
  stored at `assets/fonts/NotoSansBengali.ttf`; loads in QFontDatabase.
- **Bengali PDF export verified**: QTextDocument → QPdfWriter produced a valid PDF with
  Bengali text (`/tmp/bn-test.pdf`, 12,232 bytes, smoke test).
- argon2id hashing/verification: OK.
- Ed25519 sign/verify (cryptography): OK.
- SQLite 3.40.1: WAL mode, `connection.backup()`, `PRAGMA integrity_check`: OK.
- openpyxl workbook with Bengali cell text: OK.
- GitHub Actions Windows runners are the designated Windows build/test environment
  (first workflow run will confirm end-to-end CI capability).

## 4. Conclusions

1. Stack decision: **Python 3.11+ / PySide6 (Qt 6) / SQLite** (ADR-001). It is the only
   evaluated stack fully developable and testable inside this sandbox, with excellent
   Bengali shaping (HarfBuzz), real desktop widgets, Qt printing/PDF, and a proven
   Windows packaging path (PyInstaller + Inno Setup on `windows-latest` runners).
2. Windows installer and Windows-specific verification happen on GitHub Actions
   Windows runners; local sandbox verifies all platform-independent logic and
   offscreen UI. Physical Windows hardware (printers, scanners, display scaling)
   remains an owner-side verification item (BLOCKERS.md).
3. Brand: **Vybora Business Suite** (ভাইবোরা বিজনেস স্যুট) — matches the owner-created
   repository name; naming research in `docs/branding/BRAND_IDENTITY.md`.
