import hashlib
import os
import re
import subprocess
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile


DEFAULT_ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "text/csv": ".csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}
BLOCKED_EXTENSIONS = {".exe", ".bat", ".cmd", ".com", ".dll", ".js", ".mjs", ".php", ".ps1", ".sh", ".vbs"}
MAX_FILE_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
STORAGE_ROOT = Path(os.getenv("FILE_STORAGE_LOCAL_PATH", "storage/uploads")).resolve()
STORAGE_BACKEND = os.getenv("FILE_STORAGE_BACKEND", "local")


def _allowed_types() -> dict[str, str]:
    configured = os.getenv("ALLOWED_UPLOAD_MIME_TYPES")
    if not configured:
        return DEFAULT_ALLOWED_TYPES
    allowed = {}
    for item in configured.split(","):
        mime = item.strip()
        if mime:
            allowed[mime] = DEFAULT_ALLOWED_TYPES.get(mime, "")
    return allowed


def _safe_extension(filename: str, content_type: str) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix in BLOCKED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Blocked file extension")
    allowed = _allowed_types()
    if content_type not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported content type: {content_type}")
    expected_suffix = allowed.get(content_type)
    if expected_suffix and suffix and suffix != expected_suffix:
        raise HTTPException(status_code=400, detail="File extension does not match content type")
    return suffix or expected_suffix or ".bin"


def safe_original_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]", "_", filename or "upload")
    return cleaned[:180] or "upload"


def _scan_file(path: Path) -> tuple[str, str | None]:
    if path.read_bytes().find(b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE") >= 0:
        return "infected", "EICAR test signature detected"
    command = os.getenv("CLAMAV_SCAN_COMMAND")
    if not command:
        return "not_configured", None
    try:
        result = subprocess.run([command, str(path)], capture_output=True, text=True, timeout=30, check=False)
    except Exception as exc:
        return "scan_failed", str(exc)[:500]
    if result.returncode == 0:
        return "clean", (result.stdout or "").strip()[:500] or None
    return "infected", ((result.stdout or "") + (result.stderr or "")).strip()[:500] or "scanner rejected file"


async def store_upload(upload: UploadFile, school_id: int | None) -> dict:
    content_type = upload.content_type or "application/octet-stream"
    extension = _safe_extension(upload.filename or "", content_type)
    original_filename = safe_original_filename(upload.filename or f"upload{extension}")
    school_part = str(school_id or "platform")
    target_dir = STORAGE_ROOT / school_part
    target_dir.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid4().hex}{extension}"
    target_path = (target_dir / stored_filename).resolve()
    if not str(target_path).startswith(str(target_dir.resolve())):
        raise HTTPException(status_code=400, detail="Invalid storage path")

    digest = hashlib.sha256()
    size = 0
    with target_path.open("wb") as out:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_FILE_BYTES:
                out.close()
                target_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="File too large")
            digest.update(chunk)
            out.write(chunk)

    scan_status, scan_details = _scan_file(target_path)
    if scan_status == "infected":
        target_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="File rejected by antivirus scan")

    return {
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "content_type": content_type,
        "file_extension": extension,
        "size_bytes": size,
        "checksum_sha256": digest.hexdigest(),
        "storage_backend": STORAGE_BACKEND,
        "storage_path": str(target_path),
        "scan_status": scan_status,
        "scan_details": scan_details,
    }


def open_stored_file(storage_path: str) -> Path:
    path = Path(storage_path).resolve()
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Stored file not found")
    if STORAGE_BACKEND == "local" and not str(path).startswith(str(STORAGE_ROOT)):
        raise HTTPException(status_code=403, detail="Invalid storage path")
    return path
