# remediation/page.tsx — AI remediation page (automation D, teachers)

## Purpose

Teacher page ("Remédiation IA") over `/automations/remediation/*`: a table of
recent assessments with grade stats (grades count, average, struggling badge),
a threshold input (% of max score), and a per-row Generate button.

## Behaviour

- `POST /automations/remediation/{id}/run?threshold_ratio=` generates one
  practice set per struggling student (server-side idempotent) and the result
  card lists each generated sheet in an expandable `<details>` block
  (student, score, full practice set).
- The result hint surfaces generated / already-served / above-threshold
  counts so re-runs are understandable.
- All copy via `useTranslations("remediation")` (FR/EN/ES/SW parity).

## Verification

- `cmd.exe /c "cd frontend&& npx eslint app/[locale]/dashboard/remediation/page.tsx"`
- Backend contract: `python -m pytest backend/test_remediation.py`.
