# page.tsx (Scolarité → Diplômes & certificats)
## Source File
- `frontend/app/[locale]/dashboard/education/document-templates/page.tsx`
## Purpose
- Template management UI: kind filter, card list (default ring, active badge,
  background name), create/edit form with clickable {{placeholder}} chips inserted at
  the caret, preview (blob download), duplicate/set-default/activate/delete(confirm),
  background upload (accept .pdf/.docx/.png/.jpg), and a Generate panel (student from
  /students via student_profile.id, template or school default + kind, overrides
  training/director/graduation_date → QR-stamped PDF download).
## Local Contracts
- i18n namespace `docTemplates` (FR/EN full; es/sw = EN). Dynamic keys cast
  (`kinds.${k}` as "kinds.diploma").
## Verification
- FE build unavailable in sandbox — verified by inspection (balance, casts, icons).
