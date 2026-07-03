# test_remediation.py — Tests for auto-remédiation (automation D)

## Coverage

- Only students below the threshold get a practice set (2 of 3 at scores
  4/8/15 over /20); notifications carry `source_type="assessment"`.
- Rerun serves nobody (`skipped_done`); a newly graded struggling student is
  served on the next run without re-serving the others.
- Tenant scope: another school's assessment → 404; student role → 403 on the
  endpoint.
- Stats listing: grades count, average and struggling count per assessment.

## Pattern

In-memory SQLite (StaticPool) + direct service/router calls. Teachers are
created with `credits=1000` (AI wallet topped up via
`ai_credits.wallet_for_user`) because generation is credit-gated; the AI
service runs in local fallback mode under tests.
