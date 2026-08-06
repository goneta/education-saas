# report_cards.py
## Source File
- `backend/services/report_cards.py`
## Purpose
- Printable bulletin (audit FONC-01): the term report existed as JSON only, so
  the central document of a school term could not be printed. `build_context`
  assembles REAL data (school, student, class, term, per-subject coefficient and
  average, overall average + mention), `attach_registry` registers the bulletin
  in the universal DocumentRegistry (idempotent per student+term, so
  regenerating keeps the same UUID) and `render_pdf` draws an A4 bulletin with
  reportlab: header, student block, subject table, overall average and mention,
  signature areas, authenticity QR and the public verify URL.
## Local Contracts
- Reuses the existing document machinery (reportlab + DocumentRegistry) — no
  parallel PDF stack. A term without grades renders an explicit bulletin rather
  than failing. QR rendering failures never block the document.
- Served by `GET /grades/reports/student/{id}/term/{id}/pdf`, which enforces the
  same authorization as the JSON report (access_scope).
## Verification
- `python -m pytest backend/test_report_cards.py` (5 green).
- Seconde passe (BUG-B): `registry_source_id(student_id, term_id)` remplace la concatenation `int(f'{eleve}{trimestre}')` qui provoquait des collisions (eleve 1/trim 23 et eleve 12/trim 3 -> 123): deux eleves partageaient une entree d authenticite, le QR de l un renvoyant aux donnees de l autre.
