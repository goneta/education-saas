# api-errors.ts
## Source File
- `frontend/lib/api-errors.ts`
## Purpose
- Shared parser turning ANY API error payload into `{message, fieldErrors}` —
  the app-wide fix for "[object Object]". Handles FastAPI `detail` as string
  (HTTPException), as an ARRAY of `{loc, msg, type}` (422 validation → per-field
  errors keyed by the last snake_case loc segment + a readable joined message,
  with common Pydantic messages translated to French), and as an object
  (msg/message/JSON fallback). `parseApiErrorResponse(response, fallback)` decodes
  a !ok fetch Response (401 → session-expirée message).
## Local Contracts
- NEVER pass `payload.detail` straight to `new Error()` in form components —
  route it through this parser; map API field names to form state keys via a
  per-form `API_FIELD_TO_FORM` record (see students modals).
## Verification
- Type-check by inspection (no node_modules in sandbox); consumed by
  `components/students/add-student-modal.tsx` and `edit-student-modal.tsx`.
