# require-context.tsx

## Purpose

- Guard for school-scoped module pages. While the active context is loading it blocks nothing; once resolved with no active context it renders the consistent prompt "Please select an active Institution, Institution Model, and Academic Year before accessing this module." (i18n key `layout.contextRequiredMessage`).
- The message disappears automatically once a context is set, because `setContext` reloads the app with an active context.

## Maintenance Notes

- Consumes `useWorkingContext()`; must render under `WorkingContextProvider`.
- Applied centrally in `main-layout.tsx` via `CONTEXT_REQUIRED_SEGMENTS` (an allowlist of school-scoped route segments), so individual pages do not wrap themselves. Extend that set rather than scattering guards.
