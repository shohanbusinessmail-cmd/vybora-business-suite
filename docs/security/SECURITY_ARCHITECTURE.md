# Security Architecture — Vybora Business Suite

## 1. Authentication
- argon2id (argon2-cffi defaults: 64 MiB, t=3, p=4). Hashes stored in users.password_hash.
- Initial admin created via first-run wizard; no default/hardcoded credentials.
- Failed-attempt lockout: 5 failures → 15 min lock (configurable); counters in DB.
- Sessions: in-memory SessionContext(user_id, role perms, login ts); auto-lock after
  configurable idle timeout (UI re-login). Password change requires current password.

## 2. Authorization (RBAC, service-enforced)
Permission codes (granular): sales.view, sales.create, sales.cancel, sales.return,
costs.view, profits.view, products.manage, stock.manage, stock.adjust, customers.manage,
suppliers.manage, payments.record, purchases.manage, expenses.manage, reports.view,
users.manage, backup.manage, backup.restore, settings.manage, audit.view, license.manage.
Roles seed: owner (all), manager (all except users.manage/license.manage),
cashier (sales.*, payments.record, customers.view), inventory (products.manage,
stock.*, purchases.manage), accountant (payments.record, expenses.manage, reports.view,
costs.view, profits.view). Every service method checks permission before mutation;
UI hiding is cosmetic only. Privilege escalation blocked: only users.manage may grant
roles; audit records all permission changes.

## 3. Audit
audit_logs: ts, user, action, entity, before/after JSON (redacted: never passwords,
keys, license signatures). Actions: login/logout/failed_login, product.create/update/
deactivate, price.change, stock.adjust, sale.post/sale.reverse, payment.record,
purchase.post/reverse, expense.post/correct, return.post, backup.create/restore,
user.create/role.change, license.activate, settings.change, cash.close.

## 4. Data access
- 100% parameterized SQL (no string interpolation of values; identifiers whitelisted).
- File paths validated: imports/restores confined to chosen files; attachments copied
  into data dir with generated names (no traversal, no execution); backup restore
  accepts only files passing manifest + SQLite header + integrity + FK checks.
- Logs: structured, redacted; no SQL values, no passwords, no keys; correlation ids.

## 5. Licensing security
Ed25519 verify-only in app; fail-closed on any anomaly; public key placeholder →
unprovisioned builds reject activation. Private key only in owner generator,
encrypted at rest (argon2id + AES-256-GCM). See LICENSING_SPEC.md.

## 6. Dependency & supply chain
- Pinned versions in requirements.lock; CI runs pip-audit (PyPI advisory DB) and a
  repo secret scan (scripts/scan_secrets.py) on every push/PR and weekly schedule.
- GitHub Actions pinned to commit SHAs; least-privilege `permissions: contents: read`
  (release job elevates to contents: write only for publishing).
- No runtime network code in the app (verified by tests that monkeypatch socket).

## 7. Threat notes (honest)
- Local attacker with full machine access can patch Python bytecode → offline licensing
  is a deterrent, not a guarantee (documented for customers).
- SQLite file is not encrypted at rest in v1 (Windows account/BitLocker recommended);
  documented limitation; backup files likewise.
- Malicious backup files: rejected unless they pass structural + integrity validation;
  restore never executes SQL from the backup file (file-level swap only).

## 8. Incident handling
Security contact configurable in settings (never fabricated). SECURITY.md describes
private reporting. Key rotation procedure in KEY_CEREMONY.md.
