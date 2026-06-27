# security_middleware.py

## Source File

- `backend/security_middleware.py`

## Purpose

- Python source file used by the backend, migrations, scripts, tests, or utilities.
- HTTP middleware for security headers and rate limiting (per-IP+path window, Redis or in-memory). Rate-limit/body-size rejections `return` a `JSONResponse` (413/429) and must never `raise HTTPException`: raising inside a `BaseHTTPMiddleware` breaks the middleware chain (anyio EndOfStream) under load.
- Rate limiting is enabled only in production (`APP_ENV=production`) or when `RATE_LIMIT_ENABLED=true`; the per-process in-memory limiter is not meaningful in dev/test and is skipped there. Body-size enforcement always applies.

## DOX Scope

- Nearest contract: `backend/AGENTS.md`
- Keep this documentation understandable together with the nearest AGENTS.md and all parent AGENTS.md files.

## Maintenance Notes

- Update this sibling documentation when the source file's purpose, public contract, side effects, inputs, outputs, permissions, or verification expectations change.
- Keep the source file and this document in the same directory.

## Verification

- python -m py_compile backend\models.py backend\schemas.py backend\main.py; python -m pytest backend when relevant
