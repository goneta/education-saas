# ai_learning.py
## Source File
- `backend/routers/ai_learning.py`
## Purpose
- AI Learning Platform (`/ai-learning`): structured lesson / quiz / exam generators on the existing `ai_service` (pluggable providers, local fallback). Each generation is audit-logged.
## Local Contracts
- Educator-gated (teacher/trainer/coordinator/admin). Complements the conversational tutor (chat + 41-agent system). Image/video/speech analysis and adaptive per-student difficulty remain roadmap.
## Verification
- `python -m pytest backend/test_ai_learning.py`
