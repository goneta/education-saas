# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/page.tsx`

## Purpose

- Role-aware dashboard landing page. School users see operational school metrics, while Super Admins see a multi-establishment administration center.

## DOX Scope

- Nearest contract: `frontend/app/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Super Admin mode loads authorized schools and audit logs from system APIs, exposes `Catalogue Global` and `Gestion par établissement` tabs, and provides module links for each major sidebar rubric.
- Super Admin mode also exposes platform administration links for users, subscriptions, AI credits, AI providers, public site management, appearance, and permissions.
- School management actions may create a new establishment or toggle active/suspended status through existing Super Admin-protected system endpoints.
- The management context includes rubric, school, academic year, model, country, city, and status filters; deeper CRUD stays owned by the linked domain pages and backend RBAC.
- The academic-year selector is populated from `/context/options` (real years for the selected establishment), not a hardcoded list.
- Selecting an establishment and clicking `Activer ce contexte` calls `PUT /context/active`, scoping the whole dashboard to that school's model assignment so the Super Admin operates with its administrator's rights; the public site management link points to `/dashboard/site`.

- Super Admin section panels are independent accordions with smooth open/close animation and locally persisted state; toggling one panel must not affect the others.

## Verification

- cmd.exe /c "cd frontend&& npx eslint app/<path>"; npm run build when routes/layouts change
