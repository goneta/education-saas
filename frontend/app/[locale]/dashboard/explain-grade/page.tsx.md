# explain-grade/page.tsx — Explain-my-grade page (automation D, students)

## Purpose

Student/parent page ("Explique ma note") over `/automations/explain-grade/*`:
a table of recent grades (score badge red under half the max, class average)
with a per-row Explain button, and a result card showing the stats line
(score, class average, rank) plus the AI walk-through.

## Behaviour

- Parents get a child selector (children from `/self-documents/children`);
  students load their own grades directly.
- The explanation is requested in the CURRENT UI locale
  (`?language=${locale}` from `useLocale()`), so the walk-through matches the
  interface language.
- Generation consumes the caller's AI credits — the hint says so; a 402-style
  refusal from the credit gate surfaces in the error banner.
- All copy via `useTranslations("explainGrade")` (FR/EN/ES/SW parity).

## Verification

- `cmd.exe /c "cd frontend&& npx eslint app/[locale]/dashboard/explain-grade/page.tsx"`
- Backend contract: `python -m pytest backend/test_grade_explainer.py`.
