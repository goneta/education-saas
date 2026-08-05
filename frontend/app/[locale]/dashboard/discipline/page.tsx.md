# discipline/page.tsx
## Source File
- `frontend/app/[locale]/dashboard/discipline/page.tsx`
## Purpose
- Config-only page: passes a ModuleConfig to the generic SchoolLifeModulePage
  (components/school-life/module-page.tsx) — list/recherche/filtres/pagination/
  création/édition/suppression/export CSV/impression, gates de dépendances et
  référentiels 🌐+🏫 automatiques. Voir school_life.py (backend contract).
- Le champ Type suit la nature choisie via refCategoryBy (sanction_type / reward_type / incident_type).
