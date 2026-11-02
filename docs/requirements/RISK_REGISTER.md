# Risk Register

| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R-01 | Public repo exposes License Generator | High if committed | Critical | Gitignore + secret scan; keep generator out until private (BLK-001) | Agent/Owner |
| R-02 | Financial rounding drift | Medium | Critical | Integer poisha + value-pool costing + exhaustive unit tests + reconciliation | Agent |
| R-03 | Bengali rendering breaks in PDF/print | Medium | High | Qt HarfBuzz shaping verified; embed Noto Sans Bengali; render tests | Agent |
| R-04 | Windows-only behavior differs from Linux dev | Medium | High | windows-latest CI runs full suite + installer smoke; owner hardware checklist | Agent/Owner |
| R-05 | Data loss on crash/restore | Low | Critical | WAL+synchronous FULL, atomic txns, online backup API, validated restore, pre-restore backup | Agent |
| R-06 | License key compromise/loss | Low | Critical | Encrypted offline key, ceremony, backups, rotation procedure | Owner |
| R-07 | PyInstaller bundle flagged by AV | Medium | Medium | Document; optional code-signing certificate (owner); clean build, no obfuscation tricks | Owner |
| R-08 | Scope creep / premature release | Medium | High | 237-item checklist gate; no release until VERIFIED; honest status | Agent |
| R-09 | Performance at 100k+ rows | Medium | Medium | Indexes, virtualized tables, benchmark suite, query plans | Agent |
| R-10 | Trademark conflict on "Vybora" | Low | Medium | Naming research documented; owner legal clearance before launch | Owner |
| R-11 | Token cannot enable/verify Actions settings | Medium | Medium | Empirical first-push confirmation; owner checks repo Actions settings if blocked | Agent/Owner |
| R-12 | Offline licensing patched by determined user | Medium | Medium (revenue) | Honest limits documented; signature verification; machine binding deterrent | Owner |
