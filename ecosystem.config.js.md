# ecosystem.config.js — PM2 process definitions (TeducAI stack)

Declarative PM2 config for the TeducAI backend + frontend, portable via
`__dirname` (no hard-coded deploy path).

- `teducai-backend`: `./venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001`
  with `interpreter: "none"` — the critical bit. Without it PM2 runs the Python
  `venv/bin/uvicorn` launcher with Node and crash-loops on
  `SyntaxError: Invalid or unexpected token` (# -*- coding: utf-8 -*-).
- `teducai-frontend`: `npm start -- -p 3001` (next start) from `frontend/`, with
  `BACKEND_INTERNAL_URL=http://127.0.0.1:8001` so the Next rewrite targets THIS
  app's backend (not another app's default :8000), and NEXT_PUBLIC_API_URL unset
  so the browser uses the same-origin /api/backend proxy.

Apply: `pm2 start ecosystem.config.js && pm2 save` (+ `pm2 startup` once).
See docs/deployment-saas.md for the full reverse-proxy topology and 503 runbook.
