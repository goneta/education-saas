# attendance.py

## Source File

- `backend/routers/attendance.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities. It participates in the FastAPI API boundary.

## DOX Scope

- Nearest contract: `backend/routers/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- python -m py_compile backend\routers\<module>.py; python -c "import backend.main as m; print(m.app.title)"
# Student enrollment scope

Attendance records inherit the active student enrollment and academic-year lock enforcement.
- Seconde passe (BUG-D): `GET /attendance/` renvoyait TOUTE l assiduite de l etablissement sans limite (~700k lignes apres une annee pour 800 eleves) et sans filtrage par eleve. Desormais pagine (skip/limit, defaut 200, plafond 500, tri deterministe) et soumis a `access_scope.visible_student_ids` (eleve = ses propres releves, parent = ses enfants, personnel = l etablissement); un parametre student_id etranger ne contourne pas la regle.
