import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, schemas
from backend.routers import facilities


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school_admin(db, prefix):
    school = models.School(name=prefix, domain_prefix=f"{prefix}{uuid.uuid4().hex[:6]}", school_type=models.SchoolType.GENERAL)
    db.add(school)
    db.flush()
    admin = models.User(email=f"{prefix}_{uuid.uuid4().hex[:6]}@t.local", hashed_password="x", full_name="A", role=models.UserRole.SCHOOL_ADMIN, school=school, is_active=True)
    db.add(admin)
    db.flush()
    return school, admin


def test_room_lifecycle_with_equipment_and_building():
    db = _session()
    _school, admin = _school_admin(db, "fac")
    campus = facilities.create_campus(payload=schemas.CampusCreate(name="Campus Nord"), current_user=admin, db=db, school_id=None)
    building = facilities.create_building(payload=schemas.BuildingCreate(name="Bloc A", campus_id=campus.id), current_user=admin, db=db, school_id=None)
    room = facilities.create_room(
        payload=schemas.RoomCreate(name="Labo 1", building_id=building.id, room_type="laboratory", capacity=30,
                                   equipment=[schemas.RoomEquipmentItem(name="Paillasses", quantity=15)]),
        current_user=admin, db=db, school_id=None,
    )
    assert room.room_type == "laboratory"
    assert room.capacity == 30
    assert len(room.equipment) == 1 and room.equipment[0].name == "Paillasses"

    rooms = facilities.list_rooms(current_user=admin, db=db, school_id=None, room_type="laboratory")
    assert any(r.id == room.id for r in rooms)

    # Equipment is replaced on update.
    updated = facilities.update_room(
        room_id=room.id, payload=schemas.RoomUpdate(capacity=24, equipment=[schemas.RoomEquipmentItem(name="Ordinateurs", quantity=20)]),
        current_user=admin, db=db, school_id=None,
    )
    assert updated.capacity == 24
    assert [e.name for e in updated.equipment] == ["Ordinateurs"]


def test_rooms_isolated_by_school():
    db = _session()
    _school_a, admin_a = _school_admin(db, "faca")
    _school_b, admin_b = _school_admin(db, "facb")
    room = facilities.create_room(payload=schemas.RoomCreate(name="Salle 1"), current_user=admin_a, db=db, school_id=None)
    assert all(r.id != room.id for r in facilities.list_rooms(current_user=admin_b, db=db, school_id=None))
    with pytest.raises(HTTPException) as exc:
        facilities.delete_room(room_id=room.id, current_user=admin_b, db=db, school_id=None)
    assert exc.value.status_code == 404


def test_room_in_use_cannot_be_deleted():
    db = _session()
    _school, admin = _school_admin(db, "facuse")
    room = facilities.create_room(payload=schemas.RoomCreate(name="Salle 2"), current_user=admin, db=db, school_id=None)
    cls = models.Class(name="6A", level="6", school_id=admin.school_id)
    subject = models.Subject(name="Maths", code="M", school_id=admin.school_id)
    db.add_all([cls, subject])
    db.flush()
    from datetime import time
    db.add(models.Timetable(day_of_week=models.DayOfWeek.MONDAY, start_time=time(8, 0), end_time=time(9, 0),
                            class_id=cls.id, subject_id=subject.id, room_id=room.id))
    db.commit()
    with pytest.raises(HTTPException) as exc:
        facilities.delete_room(room_id=room.id, current_user=admin, db=db, school_id=None)
    assert exc.value.status_code == 400
