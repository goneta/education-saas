# grade_ocr.py — Grade-entry autopilot by photo (automation D, teachers)

## Purpose

- `scan_grade_sheet(db, assessment_id, school_id, current_user, *,
  image_bytes, mime_type)` — sends the photographed mark list to a
  vision-capable provider (OpenAI or Anthropic, via
  `ai_service.generate_vision_response`) with a transcription-only prompt
  (strict JSON array, skip unreadable entries), then deterministically maps
  the extracted (name, score) pairs onto the ASSESSMENT'S REAL ROSTER
  (difflib ratio on accent-stripped, order-insensitive names, threshold
  0.55). Returns proposals (student, extracted name, score, confidence,
  existing score, out-of-range flag) + unmatched entries + roster students
  missing from the photo. NOTHING is written by the scan.
- `confirm_grades(db, assessment_id, school_id, current_user, *, entries)` —
  teacher-confirmed upsert of `Grade` rows: 422 on out-of-scale scores or
  students outside the class; update-if-exists honors the
  (assessment, student) unique constraint.

## Rules

- Vision is NEVER faked: no reachable vision provider → HTTP 503 with the
  configuration hint (OPENAI_API_KEY / ANTHROPIC_API_KEY).
- Image guards: JPG/PNG/WebP only (415), 8 MB max (413).
- Credit gating: `ensure_credits(estimate + IMAGE_CREDIT_SURCHARGE)` before,
  `record_usage` after (module `automation_grade_ocr`).
- The AI only transcribes; roster mapping stays deterministic and reviewable.

## Verification

- `python -m pytest backend/test_grade_ocr.py`
