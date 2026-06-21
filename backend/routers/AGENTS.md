# Purpose

- Own FastAPI routers: request validation, dependency wiring, RBAC gates, tenant scoping, response shaping, and audit calls for API endpoints.

# Ownership

- All `backend/routers/*.py` route modules.

# Local Contracts

- Every sensitive endpoint must enforce authentication and the relevant RBAC permission before reading or mutating data.
- Queries must be scoped by tenant/school unless the route is explicitly platform-level and super-admin protected.
- Financial, document, AI, auth, role, and settings actions must record meaningful audit events when they mutate state or deny sensitive actions.
- Do not return provider secrets, password hashes, encryption keys, or internal tokens.

# Work Guidance

- Keep routers thin; move reusable business rules into `backend/services`.
- Prefer explicit error messages that are useful to users but do not leak sensitive internals.
- Preserve existing route prefixes and response shapes unless the task explicitly changes an API contract.
- Collection endpoints exposed through the Next.js proxy should accept canonical no-slash URLs without redirect; keep a hidden slash-compatible route when existing clients use it.
- Student and teacher profile ownership is the durable domain signal; do not hide valid profiles solely because a user's active primary role is an alternate learner or teaching role.

# Verification

- Targeted syntax check: `python -m py_compile backend\\routers\\<module>.py`.
- Import smoke check: `python -c "import backend.main as m; print(m.app.title)"`.
- Targeted tests: `python -m pytest backend/test_<area>.py` when available.

# Child DOX Index

- No child AGENTS.md files yet.
