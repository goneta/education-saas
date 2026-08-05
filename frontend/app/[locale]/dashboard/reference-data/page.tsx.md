# reference-data/page.tsx
## Source File
- `frontend/app/[locale]/dashboard/reference-data/page.tsx`
## Purpose
- Système → Listes de référence: category pills (?category= deep-linkable), the
  MERGED list with visual scope badges — 🌐 « Globale TeducAI » (blue, read-only
  for schools) vs 🏫 « Établissement » (green, editable by its owner) — inline
  rename, activate/deactivate, delete, and an add form (super-admin adds GLOBAL
  entries; school admin/direction add LOCAL ones with an explanatory note).
  `school_level` rows sourced from the SchoolLevel referential deep-link to the
  /levels page instead of being edited here. Errors go through lib/api-errors.
## Verification
- Backed by `/reference-data/*`; permissions enforced server-side
  (test_reference_data.py).
