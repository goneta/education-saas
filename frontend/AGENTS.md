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
- Global light/dark theme behavior is owned by `frontend/contexts/theme-context.tsx` and must stay available outside dashboard-only components.
- Dashboard top-bar notifications, theme toggle, cart, checkout, and bottom user account destinations must remain localized and backed by authenticated APIs.
- AI credit screens must distinguish platform purchases from school payments and expose cash validation or school allocation controls only to authorized roles.
- Normalize the configured API base URL and use canonical collection paths so production rewrites do not produce double slashes, 404 responses, or authorization-losing redirects.
- Shared dashboard tables expose search, sorting, pagination, reset, persisted Table/Card preference, standardized row actions, and dark-mode-safe runtime controls.
- Student, teacher, and staff profile photos must use authenticated file reads and permission-aware uploads.
- Dashboard API requests propagate the validated active school-model and academic-year context; the global selector persists changes through backend context APIs.
- Student screens treat the global student journey as the durable history and clearly distinguish local editable enrollment data from cross-school read-only academic history and hidden finance.

# Work Guidance

- Use existing Apple-inspired UI conventions: clean spacing, rounded cards, black primary actions, responsive layouts, and accessible touch targets.
- Dark mode should use the shared global theme classes and keep tables, cards, modals, forms, and dashboard shell surfaces readable without one-off page hacks where possible.
- After frontend UI changes, run targeted ESLint and, when practical, `npm run build`.
- Keep table/list action behavior consistent with standardized row actions.
- Dashboard section cards with headings should inherit the global collapsible behavior: collapsed by default, French title normalization when needed, smooth open/close, and preserved standardized row actions.
- Collapsible dashboard sections must keep independent open/closed state; toggling one section must not implicitly open, close, or remove controls from another section.
- Data-list containers may opt out of automatic collapsing with `data-teducai-collapsible="false"`; critical lists must remain visible after loading.
- Runtime-enhanced accordions and actions must receive explicit dark-theme styling because their elements are inserted after React render.
- Destructive dashboard actions must use the shared TeducAI confirmation flow; browser `alert()` and `confirm()` prompts are not allowed.

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
