# test_grade_ocr.py — Tests for the grade-entry OCR autopilot (automation D)

## Coverage

- Scan maps extracted names to the roster: "DUPONT Marie" matches
  "Marie Dupont" (order-insensitive, confidence >= 0.9), abbreviated
  "Kouassi J." still matches, an unknown name lands in `unmatched`, and the
  roster student absent from the photo lands in `missing_students`.
- Guards: non-image mime → 415; vision provider unavailable → honest 503;
  another school's assessment → 404.
- Confirm: upsert (1 created + 1 updated), scale violation → 422, student
  outside the class → 422.
- `_parse_entries` tolerates markdown fences and drops nameless/NaN rows.

## Pattern

In-memory SQLite (StaticPool) + direct service calls; the vision call is
monkeypatched (`ai_service.generate_vision_response`) because no provider key
exists in the sandbox — the mock returns the raw JSON content string exactly
as a provider would.
