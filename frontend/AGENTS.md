# Purpose

- Own the Next.js frontend for TeducAI: public pages, dashboard, mobile web app experience, i18n, UI components, auth context, layout context, E2E tests, and frontend tooling.

# Ownership

- `app/`: App Router pages, layouts, locale routes, dashboard modules, and public pages.
- `components/`: shared UI, layout, dashboard, auth, student, teacher, and library components.
- `context/` and `contexts/`: shared React state providers.
- `lib/`: frontend utilities, formatting, localization, config, and product copy.
- `messages/`: FR/EN/ES/SW translation catalogs.
- `e2e/`: Playwright scenarios.

# Local Contracts

- French is the default language; user-facing strings should go through translation/product-copy patterns where practical.
- Dashboard desktop and mobile experiences are distinct: desktop layout starts at `1024px`, mobile/tablet uses drawer/sidebar and bottom navigation patterns.
- Preserve RBAC-aware visibility and API enforcement expectations; frontend hiding is not a substitute for backend authorization.
- Avoid committing generated build logs or local `.next` artifacts.

# Work Guidance

- Use existing Apple-inspired UI conventions: clean spacing, rounded cards, black primary actions, responsive layouts, and accessible touch targets.
- After frontend UI changes, run targeted ESLint and, when practical, `npm run build`.
- Keep table/list action behavior consistent with standardized row actions.
- Dashboard section cards with headings should inherit the global collapsible behavior: collapsed by default, French title normalization when needed, smooth open/close, and preserved standardized row actions.

# Verification

- Targeted lint: `cmd.exe /c "cd frontend&& npx eslint <files>"`.
- Full build: `cmd.exe /c "cd frontend&& set NODE_OPTIONS=--max-old-space-size=4096&& npm run build"`.
- E2E: `cmd.exe /c "cd frontend&& npx playwright test"` when the relevant environment is available.

# Child DOX Index

- `app/AGENTS.md`: Next.js App Router pages, locale routing, dashboard pages, public pages, and route-local layouts.
- `components/AGENTS.md`: shared React components, dashboard shell components, UI primitives, and domain widgets.
- `lib/AGENTS.md`: frontend utility functions, config, formatting, i18n helpers, and product copy.
- `messages/AGENTS.md`: translation catalogs and default French copy.
- `e2e/AGENTS.md`: Playwright test scenarios.

Root frontend config and build tooling remain owned by this document.
