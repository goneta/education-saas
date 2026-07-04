"""In-house e-signature service (closes the last Phase-2 NOT-READY item).

Cryptographic design (no external signing provider needed):
- The document's canonical content (sorted-keys JSON of `GeneratedDocument.
  content`) is hashed with SHA-256 → `content_hash` freezes what was signed.
- The signature is an HMAC-SHA256, keyed with a signing key derived from the
  platform `SECRET_KEY` (domain-separated so JWT and signatures never share a
  raw key), over `document_id|reference|content_hash|signer_id|signed_at`.
- Verification recomputes both: an HMAC mismatch means the signature row was
  forged/corrupted; a content-hash mismatch means the DOCUMENT was modified
  after signing (tampering) even though the signature itself is authentic.

This is an integrity/authenticity signature bound to the authenticated
platform account — the audit trail (who, what, when, tamper-evidence), not a
qualified electronic signature in the eIDAS sense.
"""

import hashlib
import hmac
import json
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..security import SECRET_KEY


def _signing_key() -> bytes:
    # Domain separation: never HMAC with the raw JWT secret.
    return hashlib.sha256(f"teducai-esignature::{SECRET_KEY}".encode("utf-8")).digest()


def _content_hash(document: models.GeneratedDocument) -> str:
    canonical = json.dumps(document.content or {}, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _signature_payload(document: models.GeneratedDocument, content_hash: str, signer_id: int, signed_at_iso: str) -> bytes:
    return f"{document.id}|{document.reference or ''}|{content_hash}|{signer_id}|{signed_at_iso}".encode("utf-8")


def _compute_signature(document: models.GeneratedDocument, content_hash: str, signer_id: int, signed_at_iso: str) -> str:
    return hmac.new(_signing_key(), _signature_payload(document, content_hash, signer_id, signed_at_iso), hashlib.sha256).hexdigest()


def short_code(signature: str) -> str:
    """Human-friendly code printed on the document (first 12 hex, grouped)."""
    compact = (signature or "")[:12].upper()
    return "-".join(compact[i:i + 4] for i in range(0, len(compact), 4))


def sign_document(db: Session, document: models.GeneratedDocument, signer: models.User) -> dict:
    """Create the signer's signature over the document's current content."""
    existing = db.query(models.DocumentSignature).filter(
        models.DocumentSignature.document_id == document.id,
        models.DocumentSignature.signer_user_id == signer.id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Vous avez déjà signé ce document.")

    signed_at = datetime.utcnow()
    signed_at_iso = signed_at.isoformat()
    content_hash = _content_hash(document)
    signature = _compute_signature(document, content_hash, signer.id, signed_at_iso)

    row = models.DocumentSignature(
        document_id=document.id,
        signer_user_id=signer.id,
        signer_name=signer.full_name,
        signer_role=signer.role.value if hasattr(signer.role, "value") else str(signer.role),
        content_hash=content_hash,
        signature=signature,
        signed_at=signed_at,
    )
    db.add(row)
    db.flush()
    return signature_info(document, row)


def verify_signature(document: models.GeneratedDocument, row: models.DocumentSignature) -> dict:
    """Recompute both checks: signature authenticity + document integrity."""
    signed_at_iso = row.signed_at.isoformat() if row.signed_at else ""
    expected = _compute_signature(document, row.content_hash, row.signer_user_id, signed_at_iso)
    authentic = hmac.compare_digest(expected, row.signature or "")
    tampered = _content_hash(document) != row.content_hash
    return {"authentic": authentic, "tampered": tampered, "valid": authentic and not tampered}


def signature_info(document: models.GeneratedDocument, row: models.DocumentSignature) -> dict:
    checks = verify_signature(document, row)
    return {
        "id": row.id,
        "signer_name": row.signer_name,
        "signer_role": row.signer_role,
        "signed_at": row.signed_at,
        "code": short_code(row.signature),
        **checks,
    }


def signatures_for(db: Session, document: models.GeneratedDocument) -> list:
    rows = db.query(models.DocumentSignature).filter(models.DocumentSignature.document_id == document.id).order_by(models.DocumentSignature.id.asc()).all()
    return [signature_info(document, row) for row in rows]
