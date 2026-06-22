from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from .. import models


def document_header(db: Session, school: models.School | None) -> dict[str, Any] | None:
    if not school:
        return None
    logo = db.query(models.SecureFile).filter(
        models.SecureFile.school_id == school.id,
        models.SecureFile.entity_type == "school_logo",
        models.SecureFile.entity_id == str(school.id),
        models.SecureFile.status == "active",
        models.SecureFile.storage_backend == "local",
    ).order_by(models.SecureFile.created_at.desc(), models.SecureFile.id.desc()).first()
    logo_path = logo.storage_path if logo and Path(logo.storage_path).is_file() else None
    return {
        "name": school.name,
        "address": school.formatted_address or school.address,
        "phone": school.phone_e164 or school.phone,
        "email": school.email,
        "registration_number": school.registration_number,
        "logo_path": logo_path,
    }
