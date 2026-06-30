# page.tsx (HR › Leave)
## Source File
- `frontend/app/[locale]/dashboard/hr/leave/page.tsx`
## Purpose
- Surfaces the existing UI-less `/hr/leave-requests` backend (#1). Self-service request form (type, dates, reason) for any user; role-scoped list (admins see all, others see own) with approve/reject for approver roles. TableFilter; i18n `leave` namespace. In Gestion (admin) + the Teacher menu (self-service).
## Maintenance Notes
- Requester names resolved client-side by merging /personnel + /teachers (response has no name). Decide endpoint is approver-only server-side.
