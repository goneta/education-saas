# study-plan/page.tsx — Revision planner page (automation D, students)

## Purpose

Student/parent page ("Planning de révision") rendering
`GET /automations/study-plan`: upcoming assessments, pending homework and the
derived spaced-revision schedule grouped by day (step badge overview/practice/
final review + suggested duration).

## Behaviour

- Parents get a child selector (children fetched from
  `/self-documents/children`, same source as Mes documents); students load
  their own plan directly.
- Steps are color-coded (blue overview, amber practice, red final review).
- All copy via `useTranslations("studyPlan")` (FR/EN/ES/SW parity).

## Verification

- `cmd.exe /c "cd frontend&& npx eslint app/[locale]/dashboard/study-plan/page.tsx"`
- Backend contract: `python -m pytest backend/test_student_planner.py`.
