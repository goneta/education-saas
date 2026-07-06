# assignments.py (router) — /assignments

Teacher (EDUCATOR_ROLES): POST "" (create), POST /ai-generate, POST
/{id}/publish, GET /teaching (dashboard + stats), GET /{id}/roster (« Donner
des notes »), GET /submissions/{id}, POST /submissions/{id}/grade,
POST /submissions/{id}/ai-grade, POST /{id}/push-to-gradebook.
Student/parent: GET /mine (to-do/done/graded with own submission + answer key
when released), POST /{id}/autosave, POST /{id}/submit. School-scoped
(_resolved_school), role-gated; parent reads a linked child via student_id.
