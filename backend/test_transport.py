import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models
from backend.routers import transport


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _school_user(db, role=models.UserRole.SCHOOL_ADMIN):
    uid = uuid.uuid4().hex[:8]
    school = models.School(name=f"T {uid}", domain_prefix=f"t_{uid}", school_type=models.SchoolType.GENERAL)
    db.add(school)
    db.flush()
    user = models.User(email=f"a_{uid}@t.local", hashed_password="x", full_name="A", role=role, school_id=school.id, is_active=True)
    db.add(user)
    db.commit()
    return school, user


def test_driver_vehicle_route_assignment_flow():
    db = _session()
    school, admin = _school_user(db)

    driver = transport.create_driver(transport.schemas.TransportDriverCreate(full_name="Ali", phone="123"), db=db, current_user=admin)
    vehicle = transport.create_vehicle(transport.schemas.TransportVehicleCreate(name="Bus 1", capacity=30), db=db, current_user=admin)
    route = transport.create_route(
        transport.schemas.TransportRouteCreate(name="Route A", monthly_fee=50, driver_id=driver.id, vehicle_id=vehicle.id),
        db=db, current_user=admin,
    )
    assert route.driver_id == driver.id and route.vehicle_id == vehicle.id

    # Student in the same school can be assigned.
    student_user = models.User(email=f"s_{uuid.uuid4().hex[:6]}@t.local", hashed_password="x", full_name="S", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(student_user)
    db.flush()
    profile = models.StudentProfile(user_id=student_user.id, registration_number="R1")
    db.add(profile)
    db.commit()

    assignment = transport.create_assignment(
        transport.schemas.TransportAssignmentCreate(route_id=route.id, student_id=profile.id),
        db=db, current_user=admin,
    )
    assert assignment.id

    board = transport.dashboard(db=db, current_user=admin)
    assert board["vehicles"] == 1 and board["drivers"] == 1 and board["routes"] == 1
    assert board["students_transported"] == 1
    assert board["fleet_capacity"] == 30
    assert board["monthly_transport_revenue"] == 50


def test_bus_stops_crud_and_scoping():
    db = _session()
    school, admin = _school_user(db)
    route = transport.create_route(transport.schemas.TransportRouteCreate(name="Line 1"), db=db, current_user=admin)
    stop = transport.create_stop(
        transport.schemas.TransportStopCreate(route_id=route.id, name="Arrêt Mairie", sequence=1, latitude=5.34, longitude=-4.02, scheduled_arrival="07:15"),
        db=db, current_user=admin,
    )
    assert stop.latitude == 5.34 and stop.scheduled_arrival == "07:15"
    listed = transport.list_stops(route_id=route.id, db=db, current_user=admin)
    assert len(listed) == 1
    transport.update_stop(stop.id, transport.schemas.TransportStopUpdate(radius_m=250), db=db, current_user=admin)
    assert transport.list_stops(route_id=route.id, db=db, current_user=admin)[0].radius_m == 250
    # Dashboard reflects the stop.
    assert transport.dashboard(db=db, current_user=admin)["bus_stops"] == 1
    # Cross-school route rejected.
    _school_b, admin_b = _school_user(db)
    try:
        transport.create_stop(transport.schemas.TransportStopCreate(route_id=route.id, name="X"), db=db, current_user=admin_b)
        assert False, "stop on another school's route should be rejected"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 404


def test_assignment_rejects_cross_school_student():
    db = _session()
    school_a, admin_a = _school_user(db)
    school_b, _ = _school_user(db)
    route = transport.create_route(transport.schemas.TransportRouteCreate(name="A"), db=db, current_user=admin_a)
    # Student belongs to school B.
    other_user = models.User(email=f"o_{uuid.uuid4().hex[:6]}@t.local", hashed_password="x", full_name="O", role=models.UserRole.STUDENT, school_id=school_b.id, is_active=True)
    db.add(other_user)
    db.flush()
    foreign = models.StudentProfile(user_id=other_user.id, registration_number="RB")
    db.add(foreign)
    db.commit()
    try:
        transport.create_assignment(
            transport.schemas.TransportAssignmentCreate(route_id=route.id, student_id=foreign.id),
            db=db, current_user=admin_a,
        )
        assert False, "cross-school assignment should be rejected"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 404


def test_non_manager_cannot_write():
    db = _session()
    school, admin = _school_user(db)
    student = models.User(email=f"st_{uuid.uuid4().hex[:6]}@t.local", hashed_password="x", full_name="St", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(student)
    db.commit()
    try:
        transport.create_driver(transport.schemas.TransportDriverCreate(full_name="X"), db=db, current_user=student)
        assert False, "student should not create drivers"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403


def _student_in(db, school):
    u = models.User(email=f"s_{uuid.uuid4().hex[:6]}@t.local", hashed_password="x", full_name="S", role=models.UserRole.STUDENT, school_id=school.id, is_active=True)
    db.add(u)
    db.flush()
    p = models.StudentProfile(user_id=u.id, registration_number=f"R{uuid.uuid4().hex[:4]}")
    db.add(p)
    db.commit()
    return p


def test_gps_latest_position_per_vehicle():
    db = _session()
    school, admin = _school_user(db)
    v1 = transport.create_vehicle(transport.schemas.TransportVehicleCreate(name="V1"), db=db, current_user=admin)
    v2 = transport.create_vehicle(transport.schemas.TransportVehicleCreate(name="V2"), db=db, current_user=admin)
    transport.ingest_position(transport.schemas.TransportPositionCreate(vehicle_id=v1.id, latitude=1, longitude=1), db=db, current_user=admin)
    transport.ingest_position(transport.schemas.TransportPositionCreate(vehicle_id=v1.id, latitude=2, longitude=2), db=db, current_user=admin)
    transport.ingest_position(transport.schemas.TransportPositionCreate(vehicle_id=v2.id, latitude=9, longitude=9), db=db, current_user=admin)
    latest = transport.latest_positions(db=db, current_user=admin)
    assert len(latest) == 2  # one per vehicle
    by_vehicle = {p.vehicle_id: p for p in latest}
    assert by_vehicle[v1.id].latitude == 2  # most recent sample wins


def test_boarding_and_safety_alert():
    db = _session()
    school, admin = _school_user(db)
    route = transport.create_route(transport.schemas.TransportRouteCreate(name="R"), db=db, current_user=admin)
    boarded = _student_in(db, school)
    not_boarded = _student_in(db, school)
    for profile in (boarded, not_boarded):
        transport.create_assignment(transport.schemas.TransportAssignmentCreate(route_id=route.id, student_id=profile.id), db=db, current_user=admin)
    transport.record_boarding(transport.schemas.TransportBoardingCreate(student_id=boarded.id, route_id=route.id), db=db, current_user=admin)
    alerts = transport.safety_alerts(db=db, current_user=admin)
    flagged = {entry["student_id"] for entry in alerts["not_boarded"]}
    assert not_boarded.id in flagged and boarded.id not in flagged


def test_incidents_and_fuel_feed_dashboard():
    db = _session()
    school, admin = _school_user(db)
    vehicle = transport.create_vehicle(transport.schemas.TransportVehicleCreate(name="Bus", capacity=40), db=db, current_user=admin)
    transport.create_incident(transport.schemas.TransportIncidentCreate(incident_type="breakdown", severity="high"), db=db, current_user=admin)
    transport.create_fuel_log(transport.schemas.TransportFuelLogCreate(vehicle_id=vehicle.id, liters=50, cost=40000), db=db, current_user=admin)
    board = transport.dashboard(db=db, current_user=admin)
    assert board["open_incidents"] == 1
    assert board["fuel_cost_total"] == 40000


def test_route_optimizer_returns_advice():
    db = _session()
    school, admin = _school_user(db)
    route = transport.create_route(transport.schemas.TransportRouteCreate(name="Opt"), db=db, current_user=admin)
    transport.create_stop(transport.schemas.TransportStopCreate(route_id=route.id, name="A", sequence=1), db=db, current_user=admin)
    transport.create_stop(transport.schemas.TransportStopCreate(route_id=route.id, name="B", sequence=2), db=db, current_user=admin)
    result = transport.optimize_route(route.id, db=db, current_user=admin)
    assert result["route_id"] == route.id
    assert len(result["current_stops"]) == 2
    assert result["advice"]  # local fallback still returns a message


def test_boarding_emits_notification_and_route_notify():
    db = _session()
    school, admin = _school_user(db)
    route = transport.create_route(transport.schemas.TransportRouteCreate(name="N"), db=db, current_user=admin)
    profile = _student_in(db, school)
    transport.create_assignment(transport.schemas.TransportAssignmentCreate(route_id=route.id, student_id=profile.id), db=db, current_user=admin)
    transport.record_boarding(transport.schemas.TransportBoardingCreate(student_id=profile.id, route_id=route.id), db=db, current_user=admin)
    boarding_notifs = db.query(models.NotificationHistory).filter(models.NotificationHistory.event_type == "transport.boarding").all()
    assert len(boarding_notifs) == 1 and boarding_notifs[0].student_id == profile.id
    # Route-wide notify reaches each assigned student.
    out = transport.notify_route(route.id, subject="Retard", message="Bus en retard de 10 min", db=db, current_user=admin)
    assert out["notified"] == 1
    assert db.query(models.NotificationHistory).filter(models.NotificationHistory.event_type == "transport.route_notice").count() == 1


def test_transport_billing_generates_finance_fees_idempotently():
    db = _session()
    school, admin = _school_user(db)
    paid_route = transport.create_route(transport.schemas.TransportRouteCreate(name="Paid", monthly_fee=5000), db=db, current_user=admin)
    free_route = transport.create_route(transport.schemas.TransportRouteCreate(name="Free", monthly_fee=0), db=db, current_user=admin)
    billed = _student_in(db, school)
    unbilled = _student_in(db, school)
    transport.create_assignment(transport.schemas.TransportAssignmentCreate(route_id=paid_route.id, student_id=billed.id), db=db, current_user=admin)
    transport.create_assignment(transport.schemas.TransportAssignmentCreate(route_id=free_route.id, student_id=unbilled.id), db=db, current_user=admin)

    first = transport.generate_transport_fees(period="2026-09", db=db, current_user=admin)
    assert first["generated"] == 1 and first["skipped"] == 1  # free route skipped

    fee = db.query(models.Fee).filter(models.Fee.category == "transport").one()
    assert fee.amount == 5000 and fee.student_id == billed.id and fee.school_id == school.id
    assert fee.status == models.FeeStatus.PENDING

    # Re-running the same period does not duplicate the fee.
    second = transport.generate_transport_fees(period="2026-09", db=db, current_user=admin)
    assert second["generated"] == 0
    assert db.query(models.Fee).filter(models.Fee.category == "transport").count() == 1


def test_tenant_isolation_on_list():
    db = _session()
    school_a, admin_a = _school_user(db)
    school_b, admin_b = _school_user(db)
    transport.create_vehicle(transport.schemas.TransportVehicleCreate(name="A-bus"), db=db, current_user=admin_a)
    transport.create_vehicle(transport.schemas.TransportVehicleCreate(name="B-bus"), db=db, current_user=admin_b)
    a_vehicles = transport.list_vehicles(db=db, current_user=admin_a)
    assert len(a_vehicles) == 1 and a_vehicles[0].name == "A-bus"
