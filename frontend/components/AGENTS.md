# Purpose

- Own reusable React components, UI primitives, dashboard shell, Agent IA panel, auth components, and domain-specific widgets.

# Ownership

- All files under `frontend/components/`.

# Local Contracts

- Shared components must remain accessible, responsive, and consistent with the Apple-inspired TeducAI visual system.
- Dashboard shell components must preserve independent scrolling across desktop panels and dedicated mobile navigation.
- UI primitives should remain generic and avoid embedding module-specific data fetching.
- Components enhanced by `DashboardUxEnhancer` may opt out of automatic collapsing with `data-teducai-collapsible="false"` or opt into an initially open state with `data-teducai-default-open="true"`.
- Shared accordions, cards, and runtime-injected controls must remain readable in both light and dark themes.
- Reusable destructive confirmations use `components/ui/confirmation-dialog.tsx`; global dashboard requests are coordinated by `DashboardUxEnhancer`.

# Work Guidance

- Prefer existing primitives and lucide icons.
- Keep touch targets at least 44px for mobile-interactive controls.
- Avoid nested card-heavy designs unless the component is a true repeated item, modal, or framed tool.

# Verification

- Targeted lint: `cmd.exe /c "cd frontend&& npx eslint components/<path>.tsx"`.
- Full build when shell/layout components change.

# Child DOX Index

- No child AGENTS.md files yet.
