"""Hierarchical reference data — global TeducAI lists + per-school extensions.

One generic mechanism for every referential list of the platform:

- GLOBAL items (``school_id IS NULL``) are created/updated/deleted ONLY by the
  Super Admin and are visible to every school. Schools can neither modify nor
  delete them.
- LOCAL items belong to one school (``school_id`` set): the school's admins
  manage them and no other school ever sees them.
- Forms consume the MERGED view (:func:`merged_items`) so users see ONE list.

The ``school_level`` category is special-cased: its global part is the
EXISTING ``SchoolLevel`` referential (managed on the /levels page, zero
duplication) while local additions live here like any other category.

Adding a new referential list in the future = one entry in ``CATEGORIES``.
"""

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import audit, models

# Category registry: slug -> labels + the page where consumers create entries.
# Every category automatically gets the same permission / merge / UI behavior.
CATEGORIES: dict[str, dict[str, str]] = {
    "school_level": {"fr": "Niveaux scolaires", "en": "School levels"},
    "school_type": {"fr": "Types d'établissements", "en": "School types"},
    "fee_type": {"fr": "Types de frais scolaires", "en": "School fee types"},
    "room_type": {"fr": "Types de salles", "en": "Room types"},
    "building_type": {"fr": "Types de bâtiments", "en": "Building types"},
    "leave_type": {"fr": "Types de congés", "en": "Leave types"},
    "evaluation_type": {"fr": "Types d'évaluations", "en": "Evaluation types"},
    "document_type": {"fr": "Types de documents", "en": "Document types"},
    "sanction_type": {"fr": "Types de sanctions", "en": "Sanction types"},
    "reward_type": {"fr": "Types de récompenses", "en": "Reward types"},
    "activity_type": {"fr": "Types d'activités", "en": "Activity types"},
    "incident_type": {"fr": "Types d'incidents", "en": "Incident types"},
    "health_record_type": {"fr": "Types de dossiers santé", "en": "Health record types"},
}

# Roles allowed to manage a school's LOCAL items.
LOCAL_MANAGER_ROLES = {
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.DIRECTION,
}

GLOBAL_READONLY_DETAIL = (
    "Donnée globale TeducAI — lecture seule pour les établissements. "
    "Seul le Super Administrateur peut la modifier ou la supprimer."
)


def ensure_category(category: str) -> None:
    if category not in CATEGORIES:
        raise HTTPException(status_code=404, detail="Catégorie de référentiel inconnue.")


def _serialize(row: models.ReferenceItem) -> dict:
    return {
        "id": row.id,
        "category": row.category,
        "code": row.code,
        "name": row.name,
        "description": row.description,
        "sort_order": row.sort_order or 0,
        "is_active": bool(row.is_active),
        "scope": "school" if row.school_id else "global",
        "school_id": row.school_id,
        "source": "reference",
    }


def _serialize_level(row: models.SchoolLevel) -> dict:
    """Global school levels come from the EXISTING SchoolLevel referential."""
    return {
        "id": row.id,
        "category": "school_level",
        "code": row.code,
        "name": row.name,
        "description": getattr(row, "description", None),
        "sort_order": row.sort_order or 0,
        "is_active": bool(row.is_active),
        "scope": "global",
        "school_id": None,
        "source": "levels",  # managed on the /levels page, not editable here
    }


def merged_items(
    db: Session,
    category: str,
    school_id: Optional[int],
    *,
    include_inactive: bool = False,
) -> list[dict]:
    """The single merged list a form displays: global TeducAI + this school."""
    ensure_category(category)
    items: list[dict] = []
    seen_codes: set[str] = set()

    if category == "school_level":
        levels = db.query(models.SchoolLevel)
        if not include_inactive:
            levels = levels.filter(models.SchoolLevel.is_active == True)  # noqa: E712
        for row in levels.all():
            items.append(_serialize_level(row))
            seen_codes.add(row.code)

    query = db.query(models.ReferenceItem).filter(models.ReferenceItem.category == category)
    if not include_inactive:
        query = query.filter(models.ReferenceItem.is_active == True)  # noqa: E712
    if school_id:
        query = query.filter(
            (models.ReferenceItem.school_id == None)  # noqa: E711
            | (models.ReferenceItem.school_id == school_id)
        )
    else:
        query = query.filter(models.ReferenceItem.school_id == None)  # noqa: E711
    for row in query.all():
        if row.code in seen_codes:
            continue  # a global/local duplicate never appears twice in the UI
        items.append(_serialize(row))
        seen_codes.add(row.code)

    items.sort(key=lambda item: (item["sort_order"], item["name"].lower()))
    return items


def _resolve_write_scope(current_user: models.User, requested_scope: Optional[str],
                         school_id: Optional[int]) -> Optional[int]:
    """Which school_id a new item gets. Returns None for a GLOBAL item.

    Super Admin: global by default (or a specific school when asked).
    School admin/direction: ALWAYS local to their own school — a school can
    never write into the global TeducAI list.
    """
    if current_user.role == models.UserRole.SUPER_ADMIN:
        if requested_scope == "school":
            target = school_id or current_user.school_id
            if not target:
                raise HTTPException(status_code=400, detail="school_id requis pour une donnée locale.")
            return target
        return None
    if current_user.role not in LOCAL_MANAGER_ROLES:
        raise HTTPException(status_code=403, detail="Non autorisé à gérer les référentiels.")
    if requested_scope == "global":
        raise HTTPException(status_code=403, detail=GLOBAL_READONLY_DETAIL)
    target = current_user.school_id
    if not target:
        raise HTTPException(status_code=400, detail="Contexte établissement requis.")
    return target


def create_item(
    db: Session,
    category: str,
    *,
    current_user: models.User,
    name: str,
    code: Optional[str] = None,
    description: Optional[str] = None,
    sort_order: int = 0,
    scope: Optional[str] = None,
    school_id: Optional[int] = None,
) -> dict:
    ensure_category(category)
    clean_name = (name or "").strip()
    if not clean_name:
        raise HTTPException(status_code=422, detail="Le nom est obligatoire.")
    clean_code = (code or clean_name).strip().upper().replace(" ", "_")[:64]
    target_school_id = _resolve_write_scope(current_user, scope, school_id)

    # A code must stay unique in the school's MERGED view (and in the global
    # list for global items) so the single-list illusion never breaks.
    merged = merged_items(db, category, target_school_id or school_id, include_inactive=True)
    if any(item["code"] == clean_code for item in merged):
        raise HTTPException(status_code=409, detail="Ce code existe déjà dans cette liste.")

    row = models.ReferenceItem(
        category=category,
        code=clean_code,
        name=clean_name,
        description=description,
        sort_order=sort_order,
        school_id=target_school_id,
        created_by_id=current_user.id,
    )
    db.add(row)
    db.flush()
    audit.record_audit(
        db,
        action="reference.item.created",
        current_user=current_user,
        entity_type="reference_item",
        entity_id=row.id,
        details={"category": category, "code": clean_code,
                 "scope": "school" if target_school_id else "global",
                 "school_id": target_school_id},
    )
    return _serialize(row)


def _load_for_write(db: Session, item_id: int, current_user: models.User) -> models.ReferenceItem:
    row = db.query(models.ReferenceItem).filter(models.ReferenceItem.id == item_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Élément de référentiel introuvable.")
    if current_user.role == models.UserRole.SUPER_ADMIN:
        return row
    if row.school_id is None:
        # A school NEVER edits or deletes a global TeducAI item.
        raise HTTPException(status_code=403, detail=GLOBAL_READONLY_DETAIL)
    if current_user.role not in LOCAL_MANAGER_ROLES or current_user.school_id != row.school_id:
        raise HTTPException(status_code=403, detail="Non autorisé sur cette donnée d'établissement.")
    return row


def update_item(db: Session, item_id: int, *, current_user: models.User, data: dict) -> dict:
    row = _load_for_write(db, item_id, current_user)
    for key in ("name", "description", "sort_order", "is_active"):
        if key in data and data[key] is not None:
            setattr(row, key, data[key])
    if data.get("code"):
        row.code = str(data["code"]).strip().upper().replace(" ", "_")[:64]
    audit.record_audit(
        db,
        action="reference.item.updated",
        current_user=current_user,
        entity_type="reference_item",
        entity_id=row.id,
        details={"category": row.category, "code": row.code},
    )
    return _serialize(row)


def delete_item(db: Session, item_id: int, *, current_user: models.User) -> None:
    row = _load_for_write(db, item_id, current_user)
    audit.record_audit(
        db,
        action="reference.item.deleted",
        current_user=current_user,
        entity_type="reference_item",
        entity_id=row.id,
        details={"category": row.category, "code": row.code,
                 "scope": "school" if row.school_id else "global"},
    )
    db.delete(row)
