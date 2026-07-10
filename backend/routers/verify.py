"""Public document verification.

`GET /verify/{uuid}` is intentionally UNAUTHENTICATED: it is the endpoint a QR
code on any generated TeducAI document points to, so anyone scanning the code
can confirm the document is authentic. It returns only a safe, verifiable
summary (validity, type, school, issued-to, date, status) — never sensitive
internals beyond the snapshot the issuer chose to publish.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import database
from ..services import document_registry

router = APIRouter(prefix="/verify", tags=["Document verification"])


@router.get("/{document_uuid}")
def verify_document(document_uuid: str, db: Session = Depends(database.get_db)):
    return document_registry.verify(db, document_uuid)
