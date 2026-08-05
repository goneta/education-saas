# school_life.py
## Source File
- `backend/routers/school_life.py`
## Purpose
- FIVE Vie scolaire modules (Discipline, Examens, Activités, Santé scolaire,
  Internat) through ONE factorized CRUD engine (`_register_module`): identical
  surface under `/school-life/{slug}` — list (server-side search incl. student
  name, status/type_code/student_id filters, skip-limit pagination with exact
  total), detail, create, update, delete, `export.csv` (StreamingResponse) —
  tenant-scoped to the caller's school, every mutation audited
  (`school_life.{slug}.*`), student references validated against the school.
## Local Contracts
- Writes: SUPER_ADMIN / SCHOOL_ADMIN / DIRECTION everywhere. Reads: any school
  member EXCEPT `health` (sensitive medical data — reads restricted to the
  write roles too, `restricted_read=True`). Type codes come from the
  hierarchical reference lists (sanction/reward/incident, evaluation_type,
  activity_type, health_record_type). `exams` REUSES the existing
  `exam_sessions` table (legacy operations planning, extended column-only in
  migration 0056; type field = `exam_type`); `boarding` REUSES facilities
  `rooms` for chambers — zero duplication.
## Verification
- `python -m pytest backend/test_school_life.py` (3 green).
- PRIV-01 (audit): les lectures ne sont plus ouvertes a tout membre de l etablissement. `_scope_rows` applique `services/access_scope.visible_student_ids` aux modules porteurs de donnees personnelles (Discipline, Internat, Sante): un eleve ne voit que ses propres enregistrements, un parent ceux de ses enfants rattaches, le personnel garde la vue etablissement. Le filtrage couvre la liste, le detail (`_get_or_404(..., for_write=False)` -> 404 sur une ligne masquee), le parametre student_id et l export CSV. Examens et Activites restent visibles a tous (calendriers sans donnee personnelle), ecritures toujours reservees a l administration.
