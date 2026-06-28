"""Smart Transport module — the school-transport domain promoted out of the
generic Operations table into a first-class module.

It owns normalized master data (drivers, vehicles, routes) and the student
transport assignments that tie transport to the core platform: assignments
reference real `StudentProfile` records (single source of truth), routes carry
the monthly transport fee that flows into Finance, and the dashboard surfaces
fleet/occupancy/revenue KPIs.

GPS tracking, AI route optimization, boarding attendance, mobile apps and the
notification fan-out described in the Smart Transport architecture build on top
of this foundation; see `AGENTS.md` in this folder for the roadmap.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import database, models, schemas, security

router = APIRouter(prefix="/transport", tags=["Smart Transport"])

# Roles allowed to mutate transport master data. Reads stay open to any
# authenticated user within the tenant (mirrors the former Operations behavior).
MANAGER_ROLES = {
    models.UserRole.SUPER_ADMIN,
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.DIRECTION,
    models.UserRole.REGISTRAR,
}


def _school_id(current_user: models.User) -> int:
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    return current_user.school_id


def _ensure_manager(current_user: models.User) -> None:
    if current_user.role not in MANAGER_ROLES:
        raise HTTPException(status_code=403, detail="Not authorized")


def _scoped(db: Session, model, entity_id: int, school_id: int):
    row = db.query(model).filter(model.id == entity_id, model.school_id == school_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Introuvable")
    return row


# --------------------------------------------------------------------------- #
# Drivers
# --------------------------------------------------------------------------- #
@router.get("/drivers", response_model=List[schemas.TransportDriverResponse])
def list_drivers(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    return (
        db.query(models.TransportDriver)
        .filter(models.TransportDriver.school_id == _school_id(current_user))
        .order_by(models.TransportDriver.full_name.asc())
        .all()
    )


@router.post("/drivers", response_model=schemas.TransportDriverResponse)
def create_driver(payload: schemas.TransportDriverCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    row = models.TransportDriver(**payload.model_dump(), school_id=_school_id(current_user))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/drivers/{driver_id}", response_model=schemas.TransportDriverResponse)
def update_driver(driver_id: int, payload: schemas.TransportDriverUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    row = _scoped(db, models.TransportDriver, driver_id, _school_id(current_user))
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/drivers/{driver_id}")
def delete_driver(driver_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    row = _scoped(db, models.TransportDriver, driver_id, _school_id(current_user))
    db.delete(row)
    db.commit()
    return {"status": "deleted"}


# --------------------------------------------------------------------------- #
# Vehicles (fleet)
# --------------------------------------------------------------------------- #
@router.get("/vehicles", response_model=List[schemas.TransportVehicleResponse])
def list_vehicles(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    return (
        db.query(models.TransportVehicle)
        .filter(models.TransportVehicle.school_id == _school_id(current_user))
        .order_by(models.TransportVehicle.name.asc())
        .all()
    )


@router.post("/vehicles", response_model=schemas.TransportVehicleResponse)
def create_vehicle(payload: schemas.TransportVehicleCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    row = models.TransportVehicle(**payload.model_dump(), school_id=_school_id(current_user))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/vehicles/{vehicle_id}", response_model=schemas.TransportVehicleResponse)
def update_vehicle(vehicle_id: int, payload: schemas.TransportVehicleUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    row = _scoped(db, models.TransportVehicle, vehicle_id, _school_id(current_user))
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/vehicles/{vehicle_id}")
def delete_vehicle(vehicle_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    row = _scoped(db, models.TransportVehicle, vehicle_id, _school_id(current_user))
    db.delete(row)
    db.commit()
    return {"status": "deleted"}


# --------------------------------------------------------------------------- #
# Routes (shared TransportRoute table — same source of truth as before)
# --------------------------------------------------------------------------- #
@router.get("/routes", response_model=List[schemas.TransportRouteResponse])
def list_routes(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    return (
        db.query(models.TransportRoute)
        .filter(models.TransportRoute.school_id == _school_id(current_user))
        .order_by(models.TransportRoute.name.asc())
        .all()
    )


@router.post("/routes", response_model=schemas.TransportRouteResponse)
def create_route(payload: schemas.TransportRouteCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    school_id = _school_id(current_user)
    data = payload.model_dump()
    # Validate optional master-data links stay within the tenant.
    if data.get("driver_id"):
        _scoped(db, models.TransportDriver, data["driver_id"], school_id)
    if data.get("vehicle_id"):
        _scoped(db, models.TransportVehicle, data["vehicle_id"], school_id)
    row = models.TransportRoute(**data, school_id=school_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/routes/{route_id}", response_model=schemas.TransportRouteResponse)
def update_route(route_id: int, payload: schemas.TransportRouteCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    school_id = _school_id(current_user)
    row = _scoped(db, models.TransportRoute, route_id, school_id)
    data = payload.model_dump()
    if data.get("driver_id"):
        _scoped(db, models.TransportDriver, data["driver_id"], school_id)
    if data.get("vehicle_id"):
        _scoped(db, models.TransportVehicle, data["vehicle_id"], school_id)
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/routes/{route_id}")
def delete_route(route_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    row = _scoped(db, models.TransportRoute, route_id, _school_id(current_user))
    db.delete(row)
    db.commit()
    return {"status": "deleted"}


# --------------------------------------------------------------------------- #
# Bus stops (first-class GPS entities on a route)
# --------------------------------------------------------------------------- #
@router.get("/stops", response_model=List[schemas.TransportStopResponse])
def list_stops(route_id: int | None = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    query = db.query(models.TransportStop).filter(models.TransportStop.school_id == _school_id(current_user))
    if route_id is not None:
        query = query.filter(models.TransportStop.route_id == route_id)
    return query.order_by(models.TransportStop.route_id.asc(), models.TransportStop.sequence.asc()).all()


@router.post("/stops", response_model=schemas.TransportStopResponse)
def create_stop(payload: schemas.TransportStopCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    school_id = _school_id(current_user)
    # The stop's route must belong to the caller's tenant.
    _scoped(db, models.TransportRoute, payload.route_id, school_id)
    row = models.TransportStop(**payload.model_dump(), school_id=school_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/stops/{stop_id}", response_model=schemas.TransportStopResponse)
def update_stop(stop_id: int, payload: schemas.TransportStopUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    row = _scoped(db, models.TransportStop, stop_id, _school_id(current_user))
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/stops/{stop_id}")
def delete_stop(stop_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    row = _scoped(db, models.TransportStop, stop_id, _school_id(current_user))
    db.delete(row)
    db.commit()
    return {"status": "deleted"}


# --------------------------------------------------------------------------- #
# Student assignments (links transport to the Student Information System)
# --------------------------------------------------------------------------- #
@router.get("/assignments", response_model=List[schemas.TransportAssignmentResponse])
def list_assignments(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    return (
        db.query(models.TransportAssignment)
        .filter(models.TransportAssignment.school_id == _school_id(current_user))
        .order_by(models.TransportAssignment.id.desc())
        .all()
    )


@router.post("/assignments", response_model=schemas.TransportAssignmentResponse)
def create_assignment(payload: schemas.TransportAssignmentCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    school_id = _school_id(current_user)
    # Route and student must belong to the same tenant (no cross-school leakage).
    # StudentProfile resolves its school through the linked User account.
    _scoped(db, models.TransportRoute, payload.route_id, school_id)
    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == payload.student_id).first()
    student_user = db.query(models.User).filter(models.User.id == student.user_id).first() if student else None
    if not student or not student_user or student_user.school_id != school_id:
        raise HTTPException(status_code=404, detail="Élève introuvable dans cet établissement")
    row = models.TransportAssignment(**payload.model_dump(), school_id=school_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/assignments/{assignment_id}")
def delete_assignment(assignment_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    row = _scoped(db, models.TransportAssignment, assignment_id, _school_id(current_user))
    db.delete(row)
    db.commit()
    return {"status": "deleted"}


# --------------------------------------------------------------------------- #
# Dashboard / KPIs
# --------------------------------------------------------------------------- #
@router.get("/dashboard")
def dashboard(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    school_id = _school_id(current_user)
    routes = db.query(models.TransportRoute).filter(models.TransportRoute.school_id == school_id).all()
    vehicles = db.query(models.TransportVehicle).filter(models.TransportVehicle.school_id == school_id).all()
    drivers = db.query(models.TransportDriver).filter(models.TransportDriver.school_id == school_id).all()
    assignments = db.query(models.TransportAssignment).filter(
        models.TransportAssignment.school_id == school_id,
        models.TransportAssignment.is_active == True,  # noqa: E712
    ).all()
    capacity = sum(vehicle.capacity or 0 for vehicle in vehicles)
    transported = len(assignments)
    monthly_revenue = sum(
        (route.monthly_fee or 0)
        for assignment in assignments
        for route in routes
        if route.id == assignment.route_id
    )
    stops = db.query(models.TransportStop).filter(models.TransportStop.school_id == school_id).count()
    return {
        "vehicles": len(vehicles),
        "drivers": len(drivers),
        "routes": len(routes),
        "bus_stops": stops,
        "students_transported": transported,
        "fleet_capacity": capacity,
        "occupancy_rate": round((transported / capacity) * 100, 1) if capacity else 0,
        "monthly_transport_revenue": monthly_revenue,
        "active_routes": sum(1 for route in routes if route.is_active),
        "vehicles_in_maintenance": sum(1 for vehicle in vehicles if vehicle.status == "maintenance"),
    }
