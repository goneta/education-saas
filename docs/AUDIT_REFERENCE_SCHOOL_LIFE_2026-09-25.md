# Reference and school-life regression audit

## Reproduced defects

- After incorporating three newer commits from `origin/main`, the public API v2
  addition was found to redeclare core Pydantic classes. In particular,
  `SchoolCreate` lost `country_code`, making school registration return 500 and
  cascading into dozens of backend tests. Namespaced `PublicV2*` request models
  restore the original core bindings and keep partner endpoints typed.

- Reference updates accepted codes already used in the merged list. Deduplication
  could hide an entry from school forms. Create and update now reject conflicts
  with 409, including inactive rows, legacy levels and global/local collisions.
- Reference updates accepted whitespace-only names. Required names and codes now
  return 422 before any field mutation. Typed POST/PATCH requests also reject
  malformed values instead of reaching Python conversions or SQL binding errors.
- All five school-life modules allowed PATCH to clear required fields. Five
  independent HTTP tests reproduced the resulting SQL constraint errors. Shared
  validation now returns 422 while preserving the record.

## Verification

- Reference suites: 24 passing cases (19 new), isolated SQLite databases.
- The first full backend run passed 637 tests in 189.52 seconds, before the new
  school-life suite was collected.
- School-life suite: 12 scenarios per module, 60 total. Its initial run produced
  55 passes and 5 failures, all for clearing mandatory fields with PATCH.
- Before integrating newer remote commits, the full backend suite passed:
  697 tests, 0 failures, 153.31 seconds. After integrating and fixing the
  partner API v2 schema collision, the complete suite passed again: 707 tests,
  0 failures, 184.23 seconds. Deprecation warnings remain (2236 warnings).

## Scope and remaining checks

- No database migration or frontend dependency installation in this change.
- `frontend/node_modules` remains absent as requested.
- Ten meaningful tests per feature across the entire application remains an
  unfinished requirement. GET smoke cases do not establish functional coverage.
- Browser behavior, production PostgreSQL, concurrent reference writes, existing
  duplicate-code cleanup, load, backup restore and live operator payments are not
  established by these SQLite tests. Reference uniqueness checks are application
  checks, not a new database concurrency constraint.
