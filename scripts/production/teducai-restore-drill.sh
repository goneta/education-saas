#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${ENV_FILE:-.env.production}"
BACKUP_FILE="${1:-${BACKUP_FILE:-}}"

if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  set -a && source "$ENV_FILE" && set +a
fi

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: bash scripts/production/teducai-restore-drill.sh /path/to/backup.dump"
  echo "This script restores only when ALLOW_RESTORE=true is set."
  exit 2
fi

: "${DATABASE_URL:?DATABASE_URL must point to an isolated restore-test database, not production}"

if [ "${ALLOW_RESTORE:-false}" != "true" ]; then
  echo "Set ALLOW_RESTORE=true to run restore drill."
  exit 2
fi

echo "[WARN] Restoring $BACKUP_FILE into DATABASE_URL=$DATABASE_URL"
echo "[WARN] Make sure this is an isolated restore-test database."

BACKUP_FILE="$BACKUP_FILE" ALLOW_RESTORE=true python -m backend.scripts.restore_database
python -m alembic current

echo "[OK] Restore drill completed"
