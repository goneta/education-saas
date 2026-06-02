#!/usr/bin/env bash
set -euo pipefail

APP_URL="${1:-${APP_URL:-https://teducai.com}}"

printf '[INFO] Smoke testing %s\n' "$APP_URL"

curl -fsSI "$APP_URL" >/dev/null
printf '[OK] Homepage responds\n'

curl -fsS "$APP_URL/fr" >/dev/null
printf '[OK] French landing page responds\n'

curl -fsS "$APP_URL/fr/pricing" >/dev/null
printf '[OK] Pricing page responds\n'

curl -fsS "$APP_URL/fr/contact" >/dev/null
printf '[OK] Contact page responds\n'

if curl -fsS "$APP_URL/health" >/dev/null; then
  printf '[OK] Backend health endpoint responds at /health\n'
else
  printf '[WARN] /health not reachable from public URL. If API is mounted elsewhere, test that API URL separately.\n'
fi

if curl -fsS "$APP_URL/ready" >/dev/null; then
  printf '[OK] Backend readiness endpoint responds at /ready\n'
else
  printf '[WARN] /ready not reachable from public URL. If API is mounted elsewhere, test that API URL separately.\n'
fi

printf '[OK] Basic public smoke test completed\n'
