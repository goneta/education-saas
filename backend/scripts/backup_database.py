"""Create a production-friendly database backup artifact.

SQLite databases are copied directly. PostgreSQL backups use `pg_dump` when it
is available in the runtime image. The script writes metadata next to the backup
so operators can verify source, timestamp and checksum before restore.
"""

import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "backups")).resolve()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./education_saas.db")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sqlite_path(database_url: str) -> Path:
    raw = database_url.replace("sqlite:///", "", 1)
    return Path(raw).resolve()


def main() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    parsed = urlparse(DATABASE_URL)
    if DATABASE_URL.startswith("sqlite"):
        source = _sqlite_path(DATABASE_URL)
        if not source.exists():
            raise SystemExit(f"SQLite database not found: {source}")
        target = BACKUP_DIR / f"education_saas_{timestamp}.sqlite3"
        shutil.copy2(source, target)
    elif parsed.scheme.startswith("postgres"):
        target = BACKUP_DIR / f"education_saas_{timestamp}.dump"
        result = subprocess.run(["pg_dump", DATABASE_URL, "-Fc", "-f", str(target)], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise SystemExit(result.stderr or "pg_dump failed")
    else:
        raise SystemExit(f"Unsupported database URL scheme: {parsed.scheme}")

    metadata = {
        "created_at": datetime.utcnow().isoformat() + "Z",
        "database_scheme": parsed.scheme or "sqlite",
        "artifact": str(target),
        "size_bytes": target.stat().st_size,
        "sha256": _sha256(target),
    }
    metadata_path = target.with_suffix(target.suffix + ".json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
