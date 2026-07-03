# jobseeker_agents.py — Job-seeker automations (automation D)

## Purpose

- `refresh_my_cv(db, cv, current_user)` — on-demand CV auto-refresh: rebuilds
  `academic_timeline` from the student's real record (existing
  `employment.build_academic_snapshot`, only when the CV has a global
  profile), recomputes `total_experience_years` and stamps
  `last_auto_updated_at`. Same mechanic the year-closure flow uses, exposed
  to the student.
- `gap_analysis(db, job_id, cv, current_user, *, language)` — deterministic
  offer→profile diff (missing required/desired skills, languages, experience
  gap derived from `match_score`) + AI advice suggesting one concrete way to
  acquire each missing item (credit-gated, module `automation_gap_analysis`).
- `draft_cover_letter(db, job_id, cv, current_user, *, language)` — AI
  cover-letter draft (<250 words) grounded STRICTLY in the CV's real data
  (name, title, summary, skills, languages, experience, academic timeline);
  the prompt forbids inventing diplomas/employers (credit-gated, module
  `automation_cover_letter`).

## Rules

- Offers must be `published` (404 otherwise) for both AI features.
- All AI calls: `ensure_credits` before / `record_usage` after, charged to
  the student.

## Verification

- `python -m pytest backend/test_jobseeker_agents.py`
