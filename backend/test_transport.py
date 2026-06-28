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


def test_tenant_isolation_on_list():
    db = _session()
    school_a, admin_a = _school_user(db)
    school_b, admin_b = _school_user(db)
    transport.create_vehicle(transport.schemas.TransportVehicleCreate(name="A-bus"), db=db, current_user=admin_a)
    transport.create_vehicle(transport.schemas.TransportVehicleCreate(name="B-bus"), db=db, current_user=admin_b)
    a_vehicles = transport.list_vehicles(db=db, current_user=admin_a)
    assert len(a_vehicles) == 1 and a_vehicles[0].name == "A-bus"
