# recruiter_agents.py — Recruiter automations (automation D, recruiters)

## Purpose

Three recruiter-side automations built on the EXISTING deterministic match
engine (`employment.match_score` / `public_cv_payload`):

- `run_saved_search(db, search, current_user)` — saved-search agent: scores
  only CVs created/updated since the search's `last_run_at` watermark against
  the stored criteria (adapted through `_criteria_offer` into the same shape
  `match_score` expects), keeps those at/above `min_score`, and notifies the
  recruiter via ONE aggregate `EmploymentNotification`. The watermark is
  written with a 1-second overlap because DB server timestamps have second
  resolution while bound params carry microseconds — an exact watermark would
  skip rows created in the same second as the run; the overlap can only
  re-include a CV in the aggregate, never duplicate a row.
- `generate_screening_questions(db, job, current_user, *, num_questions,
  language)` — AI questionnaire grounded in the offer (skills + description),
  stored on `JobOffer.screening_questions` for reuse.
- `explain_match(db, job, cv_id, current_user, *, language)` — AI-written
  reasons for one candidate's ranking, grounded strictly in the deterministic
  `match_score` details (matched skills/languages, sector, experience) so the
  model cannot invent facts.

Both AI functions are credit-gated (`ensure_credits`/`record_usage`, modules
`automation_screening` / `automation_match_reasons`).

## Verification

- `python -m pytest backend/test_recruiter_agents.py`
