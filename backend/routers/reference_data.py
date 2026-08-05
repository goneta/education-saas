"""Hierarchical reference data API (`/reference-data`).

Every referential list of the platform behaves the same way through this one
router: schools READ the merged view (global TeducAI + their own local items)
and manage ONLY their local extensions; the Super Admin manages the global
lists. See services/reference_data.py for the rules.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import database, models, security
from ..services import reference_data

router = APIRouter(prefix="/reference-data", tags=["Reference data"])


def _caller_school_id(current_user: models.User, school_id: Optional[int]) -> Optional[int]:
    if current_user.role == models.UserRole.SUPER_ADMIN:
        return school_id or current_user.school_id
    return current_user.school_id


@router.get("/categories")
def list_categories(current_user: models.User = Depends(security.get_current_user)):
    return [
        {"key": key, "label_fr": labels["fr"], "label_en": labels["en"]}
        for key, labels in reference_data.CATEGORIES.items()
    ]


@router.get("/{category}")
def list_items(
    category: str,
    school_id: Optional[int] = None,
    include_inactive: bool = False,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    """The MERGED list (🌐 global TeducAI + 🏫 items of the caller's school)."""
    return reference_data.merged_items(
        db,
        category,
        _caller_school_id(current_user, school_id),
        include_inactive=include_inactive,
    )


@router.post("/{category}")
def create_item(
    category: str,
    payload: dict,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    """Super Admin -> global item (scope 'school' + school_id for a local one);
    school admin/direction -> ALWAYS a local item of their own school."""
    name = payload.get("name")
    if not isinstance(name, str):
        raise HTTPException(status_code=422, detail="Le nom est obligatoire.")
    item = reference_data.create_item(
        db,
        category,
        current_user=current_user,
        name=name,
        code=payload.get("code"),
        description=payload.get("description"),
        sort_order=int(payload.get("sort_order") or 0),
        scope=payload.get("scope"),
        school_id=payload.get("school_id"),
    )
    db.commit()
    return item


@router.patch("/items/{item_id}")
def update_item(
    item_id: int,
    payload: dict,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    item = reference_data.update_item(db, item_id, current_user=current_user, data=payload)
    db.commit()
    return item


@router.delete("/items/{item_id}")
def delete_item(
    item_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db),
):
    reference_data.delete_item(db, item_id, current_user=current_user)
    db.commit()
    return {"status": "deleted"}
