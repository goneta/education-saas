# academics.py

## Source File

- `backend/routers/academics.py`

## Purpose

- `/academics/students/{id}/gpa?term_id=`: automatic weighted GPA for a student (optionally a term), tenant-scoped via the student's institution.

## Verification

- `python -m pytest backend/test_academics.py`
- PRIV-02: le GPA verifie desormais `access_scope.can_view_student` en plus du perimetre etablissement (un eleve ne peut plus lire la moyenne d un camarade); acces non autorise masque en 404.
