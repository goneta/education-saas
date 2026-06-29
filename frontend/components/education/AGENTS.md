# Purpose

- Education-domain dashboard components (timetable constraints, etc.).

# Local Contracts

- Components here drive the `/education/*` backend endpoints. The timetable constraint panel's rule types/parameters must mirror `backend/services/timetable_constraints.py`; keep them in lock-step when the engine changes.

# Verification

- cmd.exe /c "cd frontend&& npx eslint components/education/<file>"; npm run build for shared/layout changes
