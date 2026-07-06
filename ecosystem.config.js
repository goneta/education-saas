// PM2 process definitions for the TeducAI stack (backend + frontend).
//
// Portable: paths derive from this file's location (`__dirname`), so it works
// wherever the repo is checked out. Apply with:
//
//   cd <repo> && source venv/bin/activate && alembic upgrade head
//   pm2 start ecosystem.config.js
//   pm2 save            # persist across reboots (also run `pm2 startup` once)
//
// Key point (this is what caused the crash loop): the backend MUST run through
// the venv's Python, not Node. `script: ./venv/bin/python` + `interpreter: none`
// makes PM2 exec `python -m uvicorn ...` directly instead of trying to parse the
// uvicorn launcher as JavaScript.

const path = require("path")

module.exports = {
  apps: [
    {
      name: "teducai-backend",
      cwd: __dirname,
      script: "./venv/bin/python",
      args: "-m uvicorn backend.main:app --host 127.0.0.1 --port 8001",
      interpreter: "none",
      autorestart: true,
      max_restarts: 10,
      env: {
        APP_ENV: "production",
      },
    },
    {
      name: "teducai-frontend",
      cwd: path.join(__dirname, "frontend"),
      script: "npm",
      args: "start -- -p 3001", // package.json "start" = next start
      autorestart: true,
      max_restarts: 10,
      env: {
        NODE_ENV: "production",
        // Next rewrites /api/backend/* to this URL. Pin it to THIS app's backend
        // so it can never fall through to another app's default :8000 backend.
        BACKEND_INTERNAL_URL: "http://127.0.0.1:8001",
        // Leave NEXT_PUBLIC_API_URL UNSET so the browser uses the same-origin
        // /api/backend path (served by Apache), not a cross-origin call.
      },
    },
  ],
}
