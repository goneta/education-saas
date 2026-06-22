# Purpose

- Own Next.js App Router routes for public pages, authentication pages, dashboard modules, mobile Agent IA route, and route-local layouts.

# Ownership

- All files under `frontend/app/`.

# Local Contracts

- Locale-aware routes must preserve the `frontend/app/[locale]` structure.
- Dashboard pages must work inside the shared dashboard layout and respect mobile/desktop behavior.
- Public pages should detect session state where applicable and route authenticated users toward the dashboard.
- The student lifecycle workspace owns transfer decisions, concurrent enrollment entry, duplicate-safe import preview/commit, and strongly confirmed academic-year closure.

# Work Guidance

- Prefer page components that compose shared components from `frontend/components`.
- Keep mobile pages usable without horizontal scrolling.
- Add help-section routing for new dashboard modules when practical.

# Verification

- Targeted lint: `cmd.exe /c "cd frontend&& npx eslint app/<path>.tsx"`.
- Build: `cmd.exe /c "cd frontend&& set NODE_OPTIONS=--max-old-space-size=4096&& npm run build"`.

# Child DOX Index

- No child AGENTS.md files yet.
