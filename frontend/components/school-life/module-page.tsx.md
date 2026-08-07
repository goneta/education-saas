# module-page.tsx
## Source File
- `frontend/components/school-life/module-page.tsx`
## Purpose
- Generic config-driven CRUD page powering the five Vie scolaire modules: ONE
  component provides list + server-side search, status/type filters, exact
  pagination, create/edit dialog, delete-with-confirm, CSV export (auth fetch →
  blob download) and print (`window.print`, chrome hidden via `print:hidden`).
  Each module page is just a `ModuleConfig` (slug, columns, fields, statuses).
- Field types: text/textarea/date/number/checkbox/select + SOURCE fields
  (student → /students via student_profile.id, class, subject, room →
  /facilities/rooms, reference → merged 🌐+🏫 `/reference-data/{category}`).
  Source fields are wrapped in `RequireOptions` (explicit missing-data message
  + quick-create button) and required empty sources disable submit via
  `missingRequired`. API errors flow through lib/api-errors (per-field +
  readable message — never "[object Object]").
## Local Contracts
- New Vie scolaire-style modules should be one backend `_register_module` call
  + one `ModuleConfig` page — no bespoke CRUD code.
## Verification
- Type-check by inspection (no node_modules in sandbox); backend contract in
  test_school_life.py.
- Référentiel piloté par une valeur: FieldSpec.refCategoryBy {field, map} — la catégorie de référence suit la valeur d un autre champ (Discipline: nature sanction/reward/incident -> sanction_type/reward_type/incident_type). Toutes les catégories mappées sont préchargées; sourceFor/labelFor résolvent la catégorie depuis le formulaire (dialogue) ou depuis la ligne (tableau); le filtre de type liste l union; changer le champ pilote réinitialise le champ dépendant (setFieldValue).
- Campagne erreurs silencieuses: le chargement des sources passe par `lib/api-client.fetchList`. Un echec n est plus confondu avec une liste vide — `sourcesLoaded` ne vaut true que si TOUT a repondu, un bandeau « Listes non chargees » explique l echec et propose de recharger, et le garde-fou « donnee manquante » ne s affiche plus par erreur (il faisait creer des doublons).
