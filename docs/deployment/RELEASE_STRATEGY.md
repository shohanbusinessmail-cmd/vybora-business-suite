# Release Strategy — Vybora Business Suite

## 1. Versioning
SemVer. `VERSION` file = single source of truth (currently 0.1.0-dev). Release tags
`vX.Y.Z` must match VERSION exactly (CI verifies). CHANGELOG.md maintained per release.

## 2. CI (every push/PR to main or arena/*)
- ubuntu-latest: ruff format check + lint, pytest unit+integration+db+licensing+security
  (offscreen Qt), pip-audit, secret scan. Upload junit/coverage artifacts.
- windows-latest: same test suite (real Qt), PyInstaller build smoke, installer build
  smoke (Inno Setup), silent install/launch/uninstall smoke in CI.

## 3. Release (tag v*.*.*)
1. Verify tag == VERSION; fail otherwise.
2. Full test suite (windows + ubuntu).
3. PyInstaller onedir win-x64 (app only; generator excluded).
4. Inno Setup installer → `Vybora-Setup-X.Y.Z-x64.exe`.
5. SHA-256 checksums + release metadata JSON (version, commit, build time, schema ver).
6. Bundle user manual PDF + third-party notices.
7. Create/update GitHub Release with artifacts + notes (only if all gates green).
8. No signing secrets anywhere in the workflow; generator never published.

## 4. Installer behavior (Inno Setup)
- Install dir: {autopf}\Vybora Business Suite (64-bit). App data: %LOCALAPPDATA%\Vybora
  (db, logs, backups, license, attachments) — never touched by install/uninstall.
- Start menu shortcut (always), desktop shortcut (optional task), app icon.
- Silent install: /SILENT /VERYSILENT /SUPPRESSMSGBOXES /NORESTART.
- Upgrade: installs over previous version, preserves data dir; uninstall removes
  binaries only (data preserved; explicit "remove data" is NOT offered by default).
- Version info embedded in EXE; installer shows version + license agreement (EULA).

## 5. Gates (no release if any fails)
All tests green · installer built · CI install/launch/uninstall smoke passed ·
checksums generated · docs present · FEATURE_CHECKLIST release items VERIFIED ·
no known critical/high defects · owner hardware checklist signed for HW items.

## 6. Artifacts
Vybora-Setup-X.Y.Z-x64.exe · SHA256SUMS.txt · release-metadata.json · user manual ·
THIRD_PARTY_NOTICES.md · release notes.

## 7. Current status
No production release yet. First release target: v1.0.0 after Phase 10/11 gates.
