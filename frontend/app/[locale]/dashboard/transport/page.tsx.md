# page.tsx

## Source File

- `frontend/app/[locale]/dashboard/transport/page.tsx`

## Purpose

- Smart Transport dashboard: fleet/driver/route counts, students transported, occupancy rate, monthly transport revenue and maintenance KPIs from `GET /transport/dashboard`.

## Maintenance Notes

- Read-only; tenant scope and figures come from the authenticated backend. Part of the school-scoped Smart Transport module (guarded by `CONTEXT_REQUIRED_SEGMENTS` "transport").
- Hub Transport = futur point d entrée TTransportAI: panneau Intégration (statut « À venir »/« Connectée » depuis /transport/integration/status, 11 capacités cibles affichées en pastilles, note que la gestion locale reste fonctionnelle). Aucune intégration réelle: architecture seulement.
