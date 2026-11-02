# Final Production Acceptance Criteria (master prompt Part 35)

A release is NOT fully verified until every item below is satisfied with evidence.
Mirrors the owner's mandatory acceptance list; tracked against FEATURE_CHECKLIST.md.

## Functional
- [ ] All mandatory modules implemented; all buttons/forms/workflows functional
- [ ] Sales, purchase calculations correct; customer/supplier/stock balances reconcile
- [ ] Financial postings balance; returns correct; reports use real data
- [ ] PDF/CSV/Excel export works; invoice printing works; cash closing works

## Database
- [ ] Migrations work; FK enforced; transactions atomic; duplicates controlled
- [ ] Large datasets tested; restart recovery tested
- [ ] Backup/restore/integrity verification work

## Licensing
- [ ] Generator is a separate executable; private key protected
- [ ] App contains only public verification material
- [ ] Valid activates; invalid/modified/wrong-machine rejected
- [ ] Hardware recovery documented; activated app works offline
- [ ] Generator excluded from customer installer

## UI
- [ ] All user-facing text Bengali; rendering correct; light mode only
- [ ] No overlap/clipping/broken layouts/invisible/misleading controls
- [ ] Forms/tables/dialogs usable; resizing & display scaling tested

## Security
- [ ] No secrets committed; argon2id; parameterized SQL; permission-controlled ops
- [ ] Audit logs work; license validation works; restore validated; deps reviewed

## Release
- [ ] Production build + installer generated and tested on Windows
- [ ] Clean install/launch/activation/offline/upgrade/data-preservation tested
- [ ] GitHub Actions release workflow works; SemVer tag + GitHub Release exist
- [ ] Installer attached; SHA-256 + release notes + Bengali user manual available

Status: NOT MET (development in progress). See PROJECT_STATUS.md.
