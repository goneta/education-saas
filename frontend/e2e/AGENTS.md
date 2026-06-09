# Purpose

- Own Playwright end-to-end tests for critical TeducAI user flows.

# Ownership

- All files under `frontend/e2e/`.

# Local Contracts

- E2E tests should cover real user paths and avoid relying on brittle visual-only selectors when stable labels or roles exist.
- Tests should respect locale-aware routing.

# Work Guidance

- Prefer focused tests for login, dashboard navigation, finance, settings, AI Agent, and tenant/RBAC critical paths.

# Verification

- Run with `cmd.exe /c "cd frontend&& npx playwright test"` when the app and backend are available.

# Child DOX Index

- No child AGENTS.md files yet.
