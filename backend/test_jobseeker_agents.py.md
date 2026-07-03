# test_jobseeker_agents.py — Tests for job-seeker automations (automation D)

## Coverage

- CV refresh stamps `last_auto_updated_at` and returns the summary (external
  CV: no timeline rebuild, experience recomputed).
- Gap analysis lists exactly the missing required skill (sql), desired skill
  (docker), language (anglais) and the 2-year experience gap, with non-empty
  AI advice.
- Cover letter returns grounded content; draft (unpublished) offers are
  hidden (404) from both AI features.
- A user without any CV/student profile → 404 on the refresh endpoint.

## Pattern

In-memory SQLite (StaticPool) + direct router/service calls; student wallets
credited (AI-gated generations); external CVs with `external_identity`.
