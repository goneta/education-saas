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

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import database, models, schemas, security
from ..services import automation
from ..services.ai_service import ai_service

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


@router.post("/routes/{route_id}/optimize")
def optimize_route(route_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """AI route optimizer: ask the configured AI provider to propose an improved
    stop order and recommendations from the route's current stops. Degrades to the
    local fallback when no provider is configured."""
    _ensure_manager(current_user)
    school_id = _school_id(current_user)
    route = _scoped(db, models.TransportRoute, route_id, school_id)
    stops = (
        db.query(models.TransportStop)
        .filter(models.TransportStop.route_id == route_id, models.TransportStop.school_id == school_id)
        .order_by(models.TransportStop.sequence.asc())
        .all()
    )
    stop_lines = [
        f"{stop.sequence}. {stop.name}"
        + (f" ({stop.latitude},{stop.longitude})" if stop.latitude is not None and stop.longitude is not None else "")
        + (f" ETA {stop.scheduled_arrival}" if stop.scheduled_arrival else "")
        for stop in stops
    ]
    prompt = (
        f"You are an AI school-bus route optimizer. Route '{route.name}' has these stops in current order:\n"
        + ("\n".join(stop_lines) if stop_lines else "(no stops defined yet)")
        + "\nPropose an improved stop order that reduces distance and travel time, and give 2-3 concrete, "
        "actionable recommendations (fuel, traffic windows, safety). Keep it short."
    )
    result = ai_service.generate_response_from_config(prompt, {"module": "transport_route_optimizer", "route_id": route_id}, db)
    return {
        "route_id": route_id,
        "current_stops": stop_lines,
        "advice": result.get("message"),
        "details": result.get("data"),
        "provider_model": result.get("model_name"),
    }


@router.post("/routes/{route_id}/notify")
def notify_route(route_id: int, subject: str = "Transport", message: str = "", db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Fan a transport notification (delay, route change, emergency) out to every
    student assigned to the route, via the platform NotificationHistory."""
    _ensure_manager(current_user)
    school_id = _school_id(current_user)
    route = _scoped(db, models.TransportRoute, route_id, school_id)
    assignments = db.query(models.TransportAssignment).filter(
        models.TransportAssignment.route_id == route_id,
        models.TransportAssignment.school_id == school_id,
        models.TransportAssignment.is_active == True,  # noqa: E712
    ).all()
    for assignment in assignments:
        automation.record_notification(
            db,
            event_type="transport.route_notice",
            subject=subject,
            message=message or f"Information transport — {route.name}",
            school_id=school_id,
            student_id=assignment.student_id,
            source_type="transport_route",
            source_id=route_id,
            current_user=current_user,
        )
    db.commit()
    return {"route_id": route_id, "notified": len(assignments)}


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


def _student_in_school(db: Session, student_id: int, school_id: int) -> models.StudentProfile:
    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == student_id).first()
    student_user = db.query(models.User).filter(models.User.id == student.user_id).first() if student else None
    if not student or not student_user or student_user.school_id != school_id:
        raise HTTPException(status_code=404, detail="Élève introuvable dans cet établissement")
    return student


# --------------------------------------------------------------------------- #
# GPS tracking (REST data layer for the GPS service)
# --------------------------------------------------------------------------- #
@router.post("/positions", response_model=schemas.TransportPositionResponse)
def ingest_position(payload: schemas.TransportPositionCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    school_id = _school_id(current_user)
    _scoped(db, models.TransportVehicle, payload.vehicle_id, school_id)
    row = models.TransportVehiclePosition(**payload.model_dump(), school_id=school_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/positions/latest", response_model=List[schemas.TransportPositionResponse])
def latest_positions(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Most recent GPS sample per vehicle for the tenant (newest first)."""
    rows = (
        db.query(models.TransportVehiclePosition)
        .filter(models.TransportVehiclePosition.school_id == _school_id(current_user))
        .order_by(models.TransportVehiclePosition.recorded_at.desc(), models.TransportVehiclePosition.id.desc())
        .all()
    )
    seen: set[int] = set()
    latest = []
    for row in rows:
        if row.vehicle_id in seen:
            continue
        seen.add(row.vehicle_id)
        latest.append(row)
    return latest


# --------------------------------------------------------------------------- #
# Boarding attendance
# --------------------------------------------------------------------------- #
@router.get("/boarding", response_model=List[schemas.TransportBoardingResponse])
def list_boarding(direction: Optional[str] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    query = db.query(models.TransportBoardingEvent).filter(models.TransportBoardingEvent.school_id == _school_id(current_user))
    if direction:
        query = query.filter(models.TransportBoardingEvent.direction == direction)
    return query.order_by(models.TransportBoardingEvent.recorded_at.desc()).all()


@router.post("/boarding", response_model=schemas.TransportBoardingResponse)
def record_boarding(payload: schemas.TransportBoardingCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    school_id = _school_id(current_user)
    student = _student_in_school(db, payload.student_id, school_id)
    if payload.route_id:
        _scoped(db, models.TransportRoute, payload.route_id, school_id)
    row = models.TransportBoardingEvent(**payload.model_dump(), school_id=school_id)
    db.add(row)
    db.flush()
    # Notify the parent: child boarded / was dropped off.
    student_user = db.query(models.User).filter(models.User.id == student.user_id).first()
    student_name = student_user.full_name if student_user else "L'élève"
    verb = "est monté(e) dans le bus" if payload.event_type == "boarded" else "est descendu(e) du bus"
    automation.record_notification(
        db,
        event_type="transport.boarding",
        subject="Transport scolaire",
        message=f"{student_name} {verb}.",
        school_id=school_id,
        student_id=payload.student_id,
        source_type="transport_boarding",
        source_id=row.id,
        current_user=current_user,
    )
    db.commit()
    db.refresh(row)
    return row


@router.get("/safety/alerts")
def safety_alerts(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """AI safety monitoring (heuristic v1): students with an active transport
    assignment who have no 'boarded' morning event recorded today. The richer
    cross-check against school attendance is a roadmap layer."""
    school_id = _school_id(current_user)
    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    assignments = db.query(models.TransportAssignment).filter(
        models.TransportAssignment.school_id == school_id,
        models.TransportAssignment.is_active == True,  # noqa: E712
    ).all()
    boarded_today = {
        event.student_id
        for event in db.query(models.TransportBoardingEvent).filter(
            models.TransportBoardingEvent.school_id == school_id,
            models.TransportBoardingEvent.direction == "morning",
            models.TransportBoardingEvent.event_type == "boarded",
            models.TransportBoardingEvent.recorded_at >= start_of_day,
        ).all()
    }
    missing = []
    for assignment in assignments:
        if assignment.student_id in boarded_today:
            continue
        student = db.query(models.StudentProfile).filter(models.StudentProfile.id == assignment.student_id).first()
        student_user = db.query(models.User).filter(models.User.id == student.user_id).first() if student else None
        missing.append({
            "student_id": assignment.student_id,
            "student_name": student_user.full_name if student_user else f"#{assignment.student_id}",
            "route_id": assignment.route_id,
            "alert": "not_boarded_morning",
        })
    return {"date": start_of_day.date().isoformat(), "not_boarded": missing, "count": len(missing)}


# --------------------------------------------------------------------------- #
# Incidents
# --------------------------------------------------------------------------- #
@router.get("/incidents", response_model=List[schemas.TransportIncidentResponse])
def list_incidents(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    return (
        db.query(models.TransportIncident)
        .filter(models.TransportIncident.school_id == _school_id(current_user))
        .order_by(models.TransportIncident.occurred_at.desc())
        .all()
    )


@router.post("/incidents", response_model=schemas.TransportIncidentResponse)
def create_incident(payload: schemas.TransportIncidentCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    row = models.TransportIncident(**payload.model_dump(), school_id=_school_id(current_user))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/incidents/{incident_id}")
def delete_incident(incident_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    row = _scoped(db, models.TransportIncident, incident_id, _school_id(current_user))
    db.delete(row)
    db.commit()
    return {"status": "deleted"}


# --------------------------------------------------------------------------- #
# Fuel logs
# --------------------------------------------------------------------------- #
@router.get("/fuel-logs", response_model=List[schemas.TransportFuelLogResponse])
def list_fuel_logs(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    return (
        db.query(models.TransportFuelLog)
        .filter(models.TransportFuelLog.school_id == _school_id(current_user))
        .order_by(models.TransportFuelLog.logged_at.desc())
        .all()
    )


@router.post("/fuel-logs", response_model=schemas.TransportFuelLogResponse)
def create_fuel_log(payload: schemas.TransportFuelLogCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    _ensure_manager(current_user)
    school_id = _school_id(current_user)
    _scoped(db, models.TransportVehicle, payload.vehicle_id, school_id)
    row = models.TransportFuelLog(**payload.model_dump(), school_id=school_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# --------------------------------------------------------------------------- #
# Finance integration — transport fees become Fee rows
# --------------------------------------------------------------------------- #
@router.post("/billing/generate")
def generate_transport_fees(period: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    """Generate transport `Fee` rows (category "transport") for every active
    assignment whose route carries a monthly fee, for the given period (e.g.
    "2026-09"). Idempotent: a student already billed for the same route+period is
    skipped, so re-running is safe. This makes transport part of the single
    Finance ledger (invoices, balances) rather than a parallel system."""
    _ensure_manager(current_user)
    school_id = _school_id(current_user)
    routes = {route.id: route for route in db.query(models.TransportRoute).filter(models.TransportRoute.school_id == school_id).all()}
    assignments = db.query(models.TransportAssignment).filter(
        models.TransportAssignment.school_id == school_id,
        models.TransportAssignment.is_active == True,  # noqa: E712
    ).all()
    generated = 0
    skipped = 0
    for assignment in assignments:
        route = routes.get(assignment.route_id)
        if not route or not route.monthly_fee:
            skipped += 1
            continue
        title = f"Transport {route.name} — {period}"
        exists = db.query(models.Fee.id).filter(
            models.Fee.school_id == school_id,
            models.Fee.student_id == assignment.student_id,
            models.Fee.category == "transport",
            models.Fee.title == title,
        ).first()
        if exists:
            skipped += 1
            continue
        db.add(models.Fee(
            title=title,
            amount=route.monthly_fee,
            description=f"Frais de transport · {period}",
            category="transport",
            status=models.FeeStatus.PENDING,
            student_id=assignment.student_id,
            school_id=school_id,
            is_required=True,
        ))
        generated += 1
    db.commit()
    return {"period": period, "generated": generated, "skipped": skipped}


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
    fuel_cost = sum(
        log.cost or 0
        for log in db.query(models.TransportFuelLog).filter(models.TransportFuelLog.school_id == school_id).all()
    )
    open_incidents = db.query(models.TransportIncident).filter(
        models.TransportIncident.school_id == school_id,
        models.TransportIncident.status == "open",
    ).count()
    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    boardings_today = db.query(models.TransportBoardingEvent).filter(
        models.TransportBoardingEvent.school_id == school_id,
        models.TransportBoardingEvent.recorded_at >= start_of_day,
    ).count()
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
        "fuel_cost_total": fuel_cost,
        "open_incidents": open_incidents,
        "boardings_today": boardings_today,
    }
