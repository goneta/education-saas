# test_grade_explainer.py — Tests for explain-my-grade (automation D)

## Coverage

- Grades listing carries class stats (average 14 over scores 12/16, best,
  class size) and the teacher's comment.
- Explanation computes rank (2/3 at 10 among 15/5) and returns non-empty
  content (local-fallback AI under tests).
- Ownership/RBAC: another student's grade → 404; unlinked parent → 403;
  teacher → 403 on the listing endpoint.
- A linked parent explains the child's grade via student_id (wallet topped up
  because generation is credit-gated).

## Pattern

In-memory SQLite (StaticPool) + direct service/router calls; AI wallets
credited via `ai_credits.wallet_for_user` where generation happens.
