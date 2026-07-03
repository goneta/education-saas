# test_sequence_builder.py — Tests for the séquence builder (automation D)

## Coverage

- Options report the (class, subject) pairs with weekly slot count (3) and
  weekly minutes (180 for 3×60-min slots) plus the current year's terms.
- Build computes sessions = slots × weeks (2×10=20), returns non-empty
  content (local-fallback AI) and records the `sequence.generated`
  notification to the teacher.
- Guards: another school's class → 404; a pair without timetable slots → 422;
  student role → 403 on the endpoints.

## Pattern

In-memory SQLite (StaticPool) + direct service/router calls; teacher wallets
credited because generation is AI-credit-gated.
