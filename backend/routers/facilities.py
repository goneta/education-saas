"""Facilities: campuses, buildings, rooms and equipment.

Schedulable resources for the timetable engine. Everything is tenant-scoped by
school and gated to timetable/operations admins. Rooms carry a type
(classroom/lab/workshop/gym/computer), capacity and equipment used by later
optimisation phases and by the `room_subject_restriction` constraint.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from .. import audit, database, models, schemas, security, tenancy

router = APIRouter(prefix="/facilities", tags=["Facilities"])

FACILITIES_ROLES = {
    models.UserRole.SUPER_ADMIN,
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.DIRECTION,
    models.UserRole.REGISTRAR,
}


def _admin(current_user: models.User) -> None:
    if current_user.role not in FACILITIES_ROLES:
        raise HTTPException(status_code=403, detail="Not authorized")


def _school(current_user: models.User, school_id: Optional[int], db: Session) -> int:
    return tenancy.resolve_school_id_for_create(current_user, school_id, db)


# --- Campuses ---------------------------------------------------------------

@router.get("/campuses", response_model=List[schemas.CampusResponse])
def list_campuses(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None):
    _admin(current_user)
    resolved = _school(current_user, school_id, db)
    return db.query(models.Campus).filter(models.Campus.school_id == resolved).order_by(models.Campus.name).all()


@router.post("/campuses", response_model=schemas.CampusResponse)
def create_campus(payload: schemas.CampusCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None):
    _admin(current_user)
    resolved = _school(current_user, school_id, db)
    row = models.Campus(school_id=resolved, **payload.model_dump())
    db.add(row)
    audit.record_audit(db, action="facilities.campus.created", current_user=current_user, entity_type="campus")
    db.commit()
    db.refresh(row)
    return row


# --- Buildings --------------------------------------------------------------

@router.get("/buildings", response_model=List[schemas.BuildingResponse])
def list_buildings(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None):
    _admin(current_user)
    resolved = _school(current_user, school_id, db)
    return db.query(models.Building).filter(models.Building.school_id == resolved).order_by(models.Building.name).all()


@router.post("/buildings", response_model=schemas.BuildingResponse)
def create_building(payload: schemas.BuildingCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None):
    _admin(current_user)
    resolved = _school(current_user, school_id, db)
    if payload.campus_id and not db.query(models.Campus.id).filter(models.Campus.id == payload.campus_id, models.Campus.school_id == resolved).first():
        raise HTTPException(status_code=404, detail="Campus not found")
    row = models.Building(school_id=resolved, **payload.model_dump())
    db.add(row)
    audit.record_audit(db, action="facilities.building.created", current_user=current_user, entity_type="building")
    db.commit()
    db.refresh(row)
    return row


# --- Rooms ------------------------------------------------------------------

def _room_or_404(db: Session, room_id: int, school_id: int) -> models.Room:
    row = db.query(models.Room).options(selectinload(models.Room.equipment)).filter(
        models.Room.id == room_id, models.Room.school_id == school_id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Room not found")
    return row


@router.get("/rooms", response_model=List[schemas.RoomResponse])
def list_rooms(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None, room_type: Optional[str] = None):
    _admin(current_user)
    resolved = _school(current_user, school_id, db)
    query = db.query(models.Room).options(selectinload(models.Room.equipment)).filter(models.Room.school_id == resolved)
    if room_type:
        query = query.filter(models.Room.room_type == room_type)
    return query.order_by(models.Room.name).all()


@router.post("/rooms", response_model=schemas.RoomResponse)
def create_room(payload: schemas.RoomCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None):
    _admin(current_user)
    resolved = _school(current_user, school_id, db)
    if payload.building_id and not db.query(models.Building.id).filter(models.Building.id == payload.building_id, models.Building.school_id == resolved).first():
        raise HTTPException(status_code=404, detail="Building not found")
    row = models.Room(
        school_id=resolved, name=payload.name, building_id=payload.building_id,
        room_type=payload.room_type, capacity=payload.capacity, is_active=payload.is_active,
    )
    db.add(row)
    db.flush()
    for item in payload.equipment:
        db.add(models.RoomEquipment(room_id=row.id, name=item.name, quantity=item.quantity))
    audit.record_audit(db, action="facilities.room.created", current_user=current_user, entity_type="room", entity_id=row.id)
    db.commit()
    return _room_or_404(db, row.id, resolved)


@router.put("/rooms/{room_id}", response_model=schemas.RoomResponse)
def update_room(room_id: int, payload: schemas.RoomUpdate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None):
    _admin(current_user)
    resolved = _school(current_user, school_id, db)
    row = _room_or_404(db, room_id, resolved)
    updates = payload.model_dump(exclude_unset=True)
    equipment = updates.pop("equipment", None)
    if updates.get("building_id") and not db.query(models.Building.id).filter(models.Building.id == updates["building_id"], models.Building.school_id == resolved).first():
        raise HTTPException(status_code=404, detail="Building not found")
    for key, value in updates.items():
        setattr(row, key, value)
    if equipment is not None:
        db.query(models.RoomEquipment).filter(models.RoomEquipment.room_id == row.id).delete()
        for item in equipment:
            db.add(models.RoomEquipment(room_id=row.id, name=item["name"], quantity=item.get("quantity", 1)))
    audit.record_audit(db, action="facilities.room.updated", current_user=current_user, entity_type="room", entity_id=row.id)
    db.commit()
    return _room_or_404(db, row.id, resolved)


@router.get("/rooms/{room_id}/classes")
def room_classes(room_id: int, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None):
    """Classes scheduled in a room (for the rooms list "Nb Classes" column + the
    "Voir" modal): each class with its level. Distinct on class_id (#6)."""
    _admin(current_user)
    resolved = _school(current_user, school_id, db)
    _room_or_404(db, room_id, resolved)
    class_ids = [
        cid for (cid,) in db.query(models.Timetable.class_id)
        .filter(models.Timetable.room_id == room_id, models.Timetable.class_id.isnot(None))
        .distinct().all()
    ]
    classes = db.query(models.Class).filter(models.Class.id.in_(class_ids or [-1])).order_by(models.Class.name).all()
    return {"room_id": room_id, "count": len(classes), "classes": [{"id": c.id, "name": c.name, "level": c.level} for c in classes]}


@router.delete("/rooms/{room_id}", status_code=204)
def delete_room(room_id: int, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(database.get_db), school_id: Optional[int] = None):
    _admin(current_user)
    resolved = _school(current_user, school_id, db)
    row = _room_or_404(db, room_id, resolved)
    if db.query(models.Timetable.id).filter(models.Timetable.room_id == row.id).first():
        raise HTTPException(status_code=409, detail="Cette salle est utilisée dans un emploi du temps ; réaffectez d'abord ces cours avant de la supprimer.")
    db.delete(row)
    audit.record_audit(db, action="facilities.room.deleted", current_user=current_user, entity_type="room", entity_id=room_id)
    db.commit()
