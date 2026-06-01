"""Restore a database backup artifact.

Set `ALLOW_RESTORE=true` intentionally before running. This guard prevents an
operator from restoring over a live database by accident.
"""

import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./education_saas.db")


def _sqlite_path(database_url: str) -> Path:
    raw = database_url.replace("sqlite:///", "", 1)
    return Path(raw).resolve()


def main() -> None:
    if os.getenv("ALLOW_RESTORE") != "true":
        raise SystemExit("Set ALLOW_RESTORE=true to restore a backup")
    backup = os.getenv("BACKUP_FILE")
    if not backup:
        raise SystemExit("BACKUP_FILE is required")
    backup_path = Path(backup).resolve()
    if not backup_path.exists():
        raise SystemExit(f"Backup not found: {backup_path}")

    parsed = urlparse(DATABASE_URL)
    if DATABASE_URL.startswith("sqlite"):
        target = _sqlite_path(DATABASE_URL)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_path, target)
    elif parsed.scheme.startswith("postgres"):
        result = subprocess.run(["pg_restore", "--clean", "--if-exists", "--dbname", DATABASE_URL, str(backup_path)], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise SystemExit(result.stderr or "pg_restore failed")
    else:
        raise SystemExit(f"Unsupported database URL scheme: {parsed.scheme}")
    print(f"Restored {backup_path}")


if __name__ == "__main__":
    main()
