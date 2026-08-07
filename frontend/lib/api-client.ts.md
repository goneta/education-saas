# api-client.ts
## Source File
- `frontend/lib/api-client.ts`
## Purpose
- Shared HTTP client designed so an error CANNOT be swallowed. The audit scan
  found 277 sites hiding failures: `if (res.ok)` with no `else` (177),
  `.then(r => r.ok ? r.json() : [])` (28) and `.catch(() => undefined)` (72).
- `fetchJson<T>` throws a readable error when the server refuses;
  `fetchList<T>` never throws but returns `{data, error, loaded}` so a screen
  can tell "empty" apart from "failed"; `emptyList()` is the initial state.
## Local Contracts
- The ternary pattern is the most toxic: it turns a 500/403 into an EMPTY LIST,
  and combined with the missing-dependency gates the app then tells the user
  "no class exists, create one" while the classes exist — the user creates
  duplicates. Any screen feeding a dropdown must use `fetchList` and surface
  `error` instead of rendering the "missing data" callout.
- Migrated so far: `components/school-life/module-page.tsx` (the 5 Vie scolaire
  modules). Remaining pages tracked in the audit report (PERF/UX follow-up).
## Verification
- Type-checked by inspection (node_modules removed on request after the npm
  audit; reinstall with `npm ci` for a build/tsc pass).
