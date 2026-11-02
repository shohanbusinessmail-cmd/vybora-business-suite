# Contributing

This is a proprietary commercial project. Development happens on the Arena working
branch `arena/08f8f729-vybora-business-suite` (fixed by the session).

## Workflow
1. Read PROJECT_STATUS.md, IMPLEMENTATION_ROADMAP.md, FEATURE_CHECKLIST.md, BLOCKERS.md.
2. Follow the layered architecture (docs/architecture/ARCHITECTURE.md); UI never
   bypasses services; financial logic lives in domain/services with tests.
3. Every feature: implementation + validation + error handling + DB integration +
   tests + audit + permissions + Bengali UI. Update the checklist honestly.
4. Run `ruff check`, `ruff format --check`, and `pytest` before committing.
5. Commit conventions: feat/fix/docs/test/build/chore/perf/security with clear scope.
6. Never commit secrets, keys, customer data, or the License Generator while the
   repository is public (see SECURITY.md, BLK-001).
7. Never mark a feature VERIFIED without passing tests and satisfied acceptance
   criteria. Never fabricate results.

## Code style
- Python 3.11+, type hints, dataclasses for value objects, integer poisha/milli-units.
- Parameterized SQL only. Bengali user-facing strings in i18n/bn.py.
- Small focused modules; no oversized files; documented public interfaces.
