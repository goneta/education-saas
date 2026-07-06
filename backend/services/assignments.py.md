# assignments.py — Homework / exercise module core

Full pedagogical loop on the existing Assignment / AssignmentSubmission tables
(extended in migration 0050, column-only). Functions:
- `create_assignment` (manual, draft), `generate_ai` (questions + answer key /
  corrigé via ai_service, credit-gated; splits into student-safe `content` and
  `answer_key`), `publish` (status + notify targeted students).
- Student: `open_submission`, `autosave` (draft), `submit` (online answers +
  attachments, attempt/late logic, lock after due unless late_penalty, notify
  teacher).
- Grading: `grade` (manual score+feedback+annotations, late penalty, notify
  student+linked parents), `ai_grade` (AI proposes score+feedback vs the answer
  key — never final; teacher confirms via grade()).
- `answer_key_visible_to_student` (never|after_due|immediate).
- `push_to_gradebook` (create/reuse an Assessment for the current term + upsert
  Grade rows from graded submissions).
- `submission_roster` (submitted/late/absent per student) and `stats`
  (submitted/graded/late counts, class average, success rate).
AI calls are credit-gated; nothing is faked (generator raises → caller 502).

## Verification
- `python -m pytest backend/test_assignments.py`
