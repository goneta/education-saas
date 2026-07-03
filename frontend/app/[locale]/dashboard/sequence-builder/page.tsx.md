# sequence-builder/page.tsx — Séquence builder page (automation D, teachers)

## Purpose

Teacher page ("Générateur de séquence") over `/automations/sequence/*`:
selectors for the (class, subject) pair (only pairs with real timetable
slots, weekly volume shown under the form) and the term, an optional topic
input, and a Generate button. The result card shows the computed stats
(slots/week × weeks ≈ sessions) and the full week-by-week sequence.

## Behaviour

- Generation is requested in the CURRENT UI locale (`useLocale()`), consumes
  AI credits (hint says so) and the sequence is also kept in the teacher's
  notifications server-side.
- All copy via `useTranslations("sequenceBuilder")` (FR/EN/ES/SW parity).

## Verification

- `cmd.exe /c "cd frontend&& npx eslint app/[locale]/dashboard/sequence-builder/page.tsx"`
- Backend contract: `python -m pytest backend/test_sequence_builder.py`.
