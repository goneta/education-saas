#!/usr/bin/env bash
set -euo pipefail

APP_URL="${APP_URL:-https://teducai.com}"
ENV_FILE="${ENV_FILE:-.env.production}"

failures=0

info() { printf '[INFO] %s\n' "$*"; }
ok() { printf '[OK] %s\n' "$*"; }
warn() { printf '[WARN] %s\n' "$*"; }
fail() { printf '[FAIL] %s\n' "$*"; failures=$((failures + 1)); }

require_env() {
  local key="$1"
  if [ -z "${!key:-}" ]; then
    fail "$key is not set"
  else
    ok "$key is set"
  fi
}

if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  set -a && source "$ENV_FILE" && set +a
  ok "Loaded $ENV_FILE"
else
  warn "$ENV_FILE not found; using current shell environment"
fi

info "Checking production environment for $APP_URL"

require_env APP_ENV
require_env DATABASE_URL
require_env JWT_SECRET_KEY
require_env FIELD_ENCRYPTION_KEY
require_env CORS_ALLOWED_ORIGINS
require_env BACKUP_DIR

if [ "${APP_ENV:-}" != "production" ]; then
  fail "APP_ENV must be production"
fi

if printf '%s' "${CORS_ALLOWED_ORIGINS:-}" | grep -q '\*'; then
  fail "CORS_ALLOWED_ORIGINS must not contain * in production"
fi

if [ "${CORS_ALLOWED_ORIGINS:-}" != "https://teducai.com" ]; then
  warn "CORS_ALLOWED_ORIGINS is '${CORS_ALLOWED_ORIGINS:-}', expected https://teducai.com unless API has a separate domain"
fi

case "${FILE_STORAGE_BACKEND:-}" in
  s3)
    require_env FILE_STORAGE_BUCKET
    require_env S3_ACCESS_KEY_ID
    require_env S3_SECRET_ACCESS_KEY
    ;;
  local)
    warn "FILE_STORAGE_BACKEND=local; ensure storage directory is backed up off-site"
    ;;
  *)
    fail "FILE_STORAGE_BACKEND must be s3 or local"
    ;;
esac

if [ -z "${CLAMAV_SCAN_COMMAND:-}" ]; then
  warn "CLAMAV_SCAN_COMMAND not set; uploaded files will not be scanned by real antivirus"
fi

if [ -z "${REDIS_URL:-}" ]; then
  warn "REDIS_URL not set; rate limiting may be process-local"
fi

if ! command -v python >/dev/null 2>&1; then
  fail "python command not found"
else
  ok "python available"
fi

if command -v psql >/dev/null 2>&1; then
  ok "psql available"
else
  warn "psql not found; PostgreSQL manual diagnostics will be limited"
fi

if command -v pg_dump >/dev/null 2>&1; then
  ok "pg_dump available"
else
  warn "pg_dump not found; backend backup script may fail for PostgreSQL"
fi

if command -v curl >/dev/null 2>&1; then
  curl -fsSI "$APP_URL" >/dev/null && ok "$APP_URL responds over HTTPS" || fail "$APP_URL is not reachable"
  curl -fsS "$APP_URL/health" >/dev/null && ok "/health responds" || warn "/health not reachable at $APP_URL/health; check API routing"
  curl -fsS "$APP_URL/ready" >/dev/null && ok "/ready responds" || warn "/ready not reachable at $APP_URL/ready; check API routing"
else
  warn "curl not found; URL checks skipped"
fi

python -m alembic current >/tmp/teducai_alembic_current.txt 2>&1 && ok "Alembic current works" || fail "Alembic current failed: $(cat /tmp/teducai_alembic_current.txt)"
python -m alembic heads >/tmp/teducai_alembic_heads.txt 2>&1 && ok "Alembic heads works" || fail "Alembic heads failed: $(cat /tmp/teducai_alembic_heads.txt)"

if [ "$failures" -gt 0 ]; then
  printf '\nProduction audit finished with %s failure(s).\n' "$failures"
  exit 1
fi

printf '\nProduction audit finished with no blocking failures. Review warnings before go-live.\n'
