# Security Policy

## Reporting a vulnerability
Please report security issues privately to the project owner via the support contact
configured in the application settings (or the owner's GitHub account
`shohanbusinessmail-cmd`). Do not open public issues for vulnerabilities. No support
contact is fabricated here; the owner must configure a real one before release.

## Supported versions
Only the latest released version receives security fixes (pre-release: none yet).

## Secret handling rules (mandatory)
- Never commit: private signing keys, passphrases, production secrets, customer
  license files, activation data, real business databases, personal customer data.
- The main application contains only the public license-verification key.
- CI workflows receive no signing secrets; the License Generator is never published.
- `scripts/scan_secrets.py` runs in CI to block accidental secret commits.

## Cryptography
- Passwords: argon2id. Licenses: Ed25519. Backups: SHA-256 integrity manifests.
- Private license key: encrypted at rest (argon2id-derived key + AES-256-GCM),
  owner machine only. See docs/licensing/KEY_CEREMONY.md.

## Known limitations (honest)
Offline software cannot guarantee anti-tamper or instant remote license revocation.
The local SQLite database is not encrypted at rest in v1; use Windows account
security / BitLocker. See docs/security/SECURITY_ARCHITECTURE.md.
