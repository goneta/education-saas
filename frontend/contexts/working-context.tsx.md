# working-context.tsx

## Purpose

- Global React provider for the active working context (institution + model assignment + academic year). Single source of truth consumed by the header `ContextSelector` and the `RequireContext` guard.
- Fetches `/context/options` and `/context/active` once on mount; exposes `{ options, active, loading, ready, refresh, setContext }`.
- `setContext` persists the choice through `PUT /context/active`, mirrors validated IDs to localStorage, dispatches `teducai:context-changed`, and reloads so every mounted module re-fetches under the new context.

## Security

- Options and the active context come exclusively from the authenticated backend, which validates every assignment and academic year against the user's tenant scope before persisting.
- `ready` distinguishes "still loading" from "resolved but no context" (backend 400/403) so guards never flash prematurely.

## Maintenance Notes

- Keep this the only place that reads/writes `/context/active`; consumers should use `useWorkingContext()` rather than fetching directly.
- The provider wraps `MainLayout`, so it is available to both the desktop and mobile shells.
