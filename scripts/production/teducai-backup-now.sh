#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${ENV_FILE:-.env.production}"

if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  set -a && source "$ENV_FILE" && set +a
fi

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BACKUP_DIR:=backups}"

mkdir -p "$BACKUP_DIR"

printf '[INFO] Creating TeducAI database backup in %s\n' "$BACKUP_DIR"
python -m backend.scripts.backup_database
printf '[OK] Backup completed\n'
