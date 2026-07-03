# test_recruiter_agents.py — Tests for recruiter automations (automation D)

## Coverage

- Saved search: matches the python/sql CV, ignores the off-sector low-score
  CV (min_score 70); immediate rerun finds nothing new (watermark; fixture
  CVs are backdated 2h to sit before it); a NEW matching CV is picked up on
  the next run; one aggregate `EmploymentNotification` per run-with-matches.
- Screening questions: stored on `JobOffer.screening_questions` with the
  request's num_questions.
- Explain match: reasons returned, grounded details include the matched
  skill; unknown CV → 404.
- Scoping: recruiter A cannot generate for recruiter B's offer (404); saved
  searches are per-recruiter (list empty for B, run → 404); unpaid recruiter
  (payment_status pending) → 402 on creation.

## Pattern

In-memory SQLite (StaticPool) + direct router/service calls; recruiter
wallets credited (AI-gated generations); external CVs with
`external_identity` so `public_cv_payload` resolves a name.
