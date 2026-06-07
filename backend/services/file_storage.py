import hashlib
import os
import re
import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile


DEFAULT_ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "text/csv": ".csv",
    "application/xml": ".xml",
    "text/xml": ".xml",
    "application/msword": ".doc",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}
BLOCKED_EXTENSIONS = {".exe", ".bat", ".cmd", ".com", ".dll", ".js", ".mjs", ".php", ".ps1", ".sh", ".vbs"}
MAX_FILE_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
STORAGE_ROOT = Path(os.getenv("FILE_STORAGE_LOCAL_PATH", "DOCUMENTS")).resolve()
STORAGE_BACKEND = os.getenv("FILE_STORAGE_BACKEND", "local")
S3_BUCKET = os.getenv("FILE_STORAGE_BUCKET", "")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
SIGNED_URL_EXPIRES_SECONDS = int(os.getenv("SIGNED_URL_EXPIRES_SECONDS", "900"))


def _s3_client():
    try:
        import boto3  # type: ignore
    except Exception as exc:
        raise HTTPException(status_code=500, detail="S3 backend requires boto3") from exc
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("S3_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1",
    )


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


def generated_document_filename(document_name: str, user_id: int, extension: str) -> str:
    base = safe_original_filename(document_name or "Document")
    base = Path(base).stem.replace(" ", "_")
    return f"{base}_user{user_id}{extension}"


async def store_upload(upload: UploadFile, school_id: int | None, document_name: str | None = None, user_id: int | None = None, folder: str = "uploads") -> dict:
    content_type = upload.content_type or "application/octet-stream"
    extension = _safe_extension(upload.filename or "", content_type)
    original_filename = generated_document_filename(document_name, user_id or 0, extension) if document_name and user_id else safe_original_filename(upload.filename or f"upload{extension}")
    stored_filename = f"{uuid4().hex}{extension}"
    school_part = f"ETABLISSEMENT{school_id}" if school_id else "PLATFORM"
    storage_key = f"{school_part}/{folder}/{stored_filename}"
    target_dir = STORAGE_ROOT / school_part / folder
    if STORAGE_BACKEND == "local":
        for required_folder in ("uploads", "generated", "shared"):
            (STORAGE_ROOT / school_part / required_folder).mkdir(parents=True, exist_ok=True)
    target_dir.mkdir(parents=True, exist_ok=True)
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

    storage_path = str(target_path)
    if STORAGE_BACKEND in {"s3", "minio"}:
        if not S3_BUCKET:
            target_path.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail="FILE_STORAGE_BUCKET is required for S3/MinIO")
        client = _s3_client()
        client.upload_file(
            str(target_path),
            S3_BUCKET,
            storage_key,
            ExtraArgs={
                "ContentType": content_type,
                "Metadata": {"sha256": digest.hexdigest(), "original-filename": original_filename[:120]},
            },
        )
        storage_path = storage_key
        target_path.unlink(missing_ok=True)

    return {
        "original_filename": original_filename,
        "display_name": document_name,
        "stored_filename": stored_filename,
        "content_type": content_type,
        "file_extension": extension,
        "size_bytes": size,
        "checksum_sha256": digest.hexdigest(),
        "storage_backend": STORAGE_BACKEND,
        "storage_path": storage_path,
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


def signed_download_url(storage_backend: str, storage_path: str, content_type: str, filename: str) -> str | None:
    if storage_backend not in {"s3", "minio"}:
        return None
    if not S3_BUCKET:
        raise HTTPException(status_code=500, detail="FILE_STORAGE_BUCKET is required for signed URLs")
    return _s3_client().generate_presigned_url(
        "get_object",
        Params={
            "Bucket": S3_BUCKET,
            "Key": storage_path,
            "ResponseContentType": content_type,
            "ResponseContentDisposition": f'attachment; filename="{safe_original_filename(filename)}"',
        },
        ExpiresIn=SIGNED_URL_EXPIRES_SECONDS,
    )


def download_s3_to_temp(storage_path: str) -> Path:
    if not S3_BUCKET:
        raise HTTPException(status_code=500, detail="FILE_STORAGE_BUCKET is required for S3/MinIO")
    suffix = Path(storage_path).suffix
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    handle.close()
    path = Path(handle.name)
    _s3_client().download_file(S3_BUCKET, storage_path, str(path))
    return path
