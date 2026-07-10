"""Universal document authenticity registry + QR helpers.

Every generated TeducAI document (invoice, report card, certificate, diploma,
payslip, ...) can be registered here, producing a public UUID, a content hash
and a type-specific JSON payload. A QR encoding that JSON + the public
verification URL is stamped on the document; the public `/verify/{uuid}` page
resolves it back to an authenticity record.

Cross-cutting, zero duplication: a registry row REFERENCES the originating
record via (source_type, source_id) and stores only a verifiable snapshot.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import uuid as _uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from .. import models
from ..audit import record_audit


def verify_base_url() -> str:
    return (os.getenv("DOCUMENT_VERIFY_BASE_URL", "https://teducai.com") or "https://teducai.com").rstrip("/")


def verification_url(document_uuid: str) -> str:
    return f"{verify_base_url()}/verify/{document_uuid}"


def _canonical(payload: Optional[dict]) -> str:
    return json.dumps(payload or {}, sort_keys=True, default=str, ensure_ascii=False)


def content_hash(payload: Optional[dict]) -> str:
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def register(
    db: Session,
    *,
    document_type: str,
    school_id: Optional[int] = None,
    title: Optional[str] = None,
    reference: Optional[str] = None,
    issued_to_name: Optional[str] = None,
    issued_to_id: Optional[int] = None,
    payload: Optional[dict] = None,
    source_type: Optional[str] = None,
    source_id: Optional[int] = None,
    issued_by: Optional[models.User] = None,
) -> models.DocumentRegistry:
    """Create (or update) an authenticity record. Idempotent per (source_type, source_id)."""
    row = None
    if source_type and source_id:
        row = (
            db.query(models.DocumentRegistry)
            .filter(models.DocumentRegistry.source_type == source_type,
                    models.DocumentRegistry.source_id == source_id)
            .first()
        )
    if row is None:
        row = models.DocumentRegistry(uuid=str(_uuid.uuid4()), document_type=document_type,
                                      source_type=source_type, source_id=source_id, status="valid")
        db.add(row)
    row.document_type = document_type
    row.school_id = school_id
    row.title = title
    row.reference = reference
    row.issued_to_name = issued_to_name
    row.issued_to_id = issued_to_id
    row.payload = payload
    row.content_hash = content_hash(payload)
    if issued_by is not None:
        row.issued_by_id = issued_by.id
    db.flush()
    return row


def qr_data(row: models.DocumentRegistry) -> dict:
    """The JSON encoded in the document's QR code."""
    data = dict(row.payload or {})
    data.update({
        "type": row.document_type,
        "uuid": row.uuid,
        "verify_url": verification_url(row.uuid),
    })
    return data


def qr_text(row: models.DocumentRegistry) -> str:
    return json.dumps(qr_data(row), ensure_ascii=False, separators=(",", ":"))


def render_qr_png(text: str, *, box_size: int = 6, border: int = 2) -> bytes:
    """Render a QR code to PNG bytes (pure-Python qrcode + Pillow)."""
    import qrcode

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=box_size, border=border)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def draw_qr_on_canvas(c, text: str, x: float, y: float, size: float) -> None:
    """Stamp a QR (top-right typically) onto a reportlab canvas at (x, y)."""
    from reportlab.lib.utils import ImageReader

    png = render_qr_png(text)
    c.drawImage(ImageReader(io.BytesIO(png)), x, y, width=size, height=size, mask="auto")


def verify(db: Session, document_uuid: str) -> dict:
    row = db.query(models.DocumentRegistry).filter(models.DocumentRegistry.uuid == document_uuid).first()
    if not row:
        return {"valid": False, "status": "not_found"}
    school = db.query(models.School).filter(models.School.id == row.school_id).first() if row.school_id else None
    return {
        "valid": row.status == "valid",
        "status": row.status,
        "uuid": row.uuid,
        "document_type": row.document_type,
        "title": row.title,
        "reference": row.reference,
        "school_name": school.name if school else (row.payload or {}).get("School Name"),
        "issued_to": row.issued_to_name,
        "date_generated": row.created_at,
        "payload": row.payload,
        "verify_url": verification_url(row.uuid),
    }


def revoke(db: Session, document_uuid: str, user: models.User) -> Optional[models.DocumentRegistry]:
    row = db.query(models.DocumentRegistry).filter(models.DocumentRegistry.uuid == document_uuid).first()
    if not row:
        return None
    row.status = "revoked"
    record_audit(db, action="document.revoked", current_user=user,
                 entity_type="document_registry", entity_id=row.id, details={"uuid": row.uuid})
    db.flush()
    return row


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")
