# grade-scan/page.tsx — Grade entry by photo (automation D, teachers)

## Purpose

Teacher page ("Saisie de notes par photo") over `/automations/grade-ocr/*`:
assessment selector (reuses the remediation stats listing), camera/file input
(`capture="environment"` opens the phone camera; JPG/PNG/WebP), then a review
table — matched student vs name read on the photo, color-coded confidence
badge (green ≥85%, amber ≥70%, red below), existing score, and an editable
score input (red border when out of scale). Unmatched names and roster
students missing from the photo are listed separately. "Confirmer et
enregistrer" posts the reviewed entries to the confirm endpoint (upsert).

## Behaviour

- Nothing is saved by the scan; only the confirm writes grades.
- 503 from a missing vision provider (OpenAI/Anthropic key) surfaces in the
  error banner; the hint under the form says which keys to configure.
- All copy via `useTranslations("gradeOcr")` (FR/EN/ES/SW parity).

## Verification

- `cmd.exe /c "cd frontend&& npx eslint app/[locale]/dashboard/grade-scan/page.tsx"`
- Backend contract: `python -m pytest backend/test_grade_ocr.py`.
