import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend import database, models, schemas
from backend.routers import payroll
from backend.services import payroll as engine


def _session():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(bind=eng)
    return sessionmaker(bind=eng)()


def _admin(db):
    uid = uuid.uuid4().hex[:8]
    school = models.School(name=f"P {uid}", domain_prefix=f"p_{uid}", school_type=models.SchoolType.GENERAL)
    db.add(school); db.flush()
    admin = models.User(email=f"a_{uid}@example.com", hashed_password="x", full_name="Admin", role=models.UserRole.SCHOOL_ADMIN, school_id=school.id, is_active=True)
    staff = models.User(email=f"s_{uid}@example.com", hashed_password="x", full_name="Awa Diop", role=models.UserRole.TEACHER, school_id=school.id, is_active=True)
    db.add_all([admin, staff]); db.commit()
    return school, admin, staff


def test_engine_breakdown_is_correct():
    lines = [
        engine.PayslipLine("allowance", "Transport", 20000),
        engine.PayslipLine("bonus", "Performance", 10000),
        engine.PayslipLine("overtime", "Heures sup", 5000),
        engine.PayslipLine("deduction", "Retenue", 3000),
        engine.PayslipLine("advance", "Avance", 7000),
    ]
    comp = engine.compute(base_amount=100000, lines=lines, cotisation_rate=0.1, tax_rate=0.2)
    assert comp.gross_amount == 135000  # 100k + 20k + 10k + 5k
    assert comp.social_contributions == 13500  # 10%
    # tax = (135000 - 13500) * 20% = 24300
    assert comp.tax_amount == 24300
    # total deductions = 13500 + 24300 + 3000 (deduction) + 7000 (advance) = 47800
    assert comp.total_deductions == 47800
    assert comp.net_amount == 135000 - 47800


def test_base_amount_for_pay_types():
    assert engine.base_amount_for("hourly", 2500, 40) == 100000
    assert engine.base_amount_for("daily", 15000, 22) == 330000
    assert engine.base_amount_for("monthly", 250000, 99) == 250000  # units ignored


def test_generate_payslip_and_self_service():
    db = _session()
    school, admin, staff = _admin(db)
    payroll.create_salary_profile(payload=schemas.SalaryProfileCreate(user_id=staff.id, pay_type="monthly", base_rate=200000, cotisation_rate=0.1, tax_rate=0.15), school_id=None, db=db, current_user=admin)
    slip = payroll.generate_payslip(
        payload=schemas.PayslipGenerate(staff_user_id=staff.id, period="2026-06", period_type="monthly", lines=[schemas.PayslipLineInput(type="allowance", label="Transport", amount=25000)]),
        school_id=None, db=db, current_user=admin,
    )
    assert slip.gross_amount == 225000 and slip.net_amount < slip.gross_amount
    assert len(slip.lines) == 1 and slip.status == models.PayrollStatus.DRAFT
    # Self-service: the teacher sees their own payslip.
    mine = payroll.my_payslips(db=db, current_user=staff)
    assert len(mine) == 1 and mine[0].id == slip.id
    # Duplicate period rejected.
    try:
        payroll.generate_payslip(payload=schemas.PayslipGenerate(staff_user_id=staff.id, period="2026-06", period_type="monthly"), school_id=None, db=db, current_user=admin)
        assert False, "duplicate period should be rejected"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 409


def test_pay_marks_paid_and_records_method():
    db = _session()
    _school, admin, staff = _admin(db)
    payroll.create_salary_profile(payload=schemas.SalaryProfileCreate(user_id=staff.id, base_rate=150000), school_id=None, db=db, current_user=admin)
    slip = payroll.generate_payslip(payload=schemas.PayslipGenerate(staff_user_id=staff.id, period="2026-07"), school_id=None, db=db, current_user=admin)
    paid = payroll.pay_payslip(record_id=slip.id, payload=schemas.PayslipPay(payment_method="cinetpay", payment_reference="TX-1"), school_id=None, db=db, current_user=admin)
    assert paid.status == models.PayrollStatus.PAID and paid.payment_method == "cinetpay" and paid.paid_at is not None


def test_non_admin_cannot_manage_but_owner_reads_own():
    db = _session()
    _school, admin, staff = _admin(db)
    payroll.create_salary_profile(payload=schemas.SalaryProfileCreate(user_id=staff.id, base_rate=100000), school_id=None, db=db, current_user=admin)
    slip = payroll.generate_payslip(payload=schemas.PayslipGenerate(staff_user_id=staff.id, period="2026-08"), school_id=None, db=db, current_user=admin)
    # Teacher cannot list everyone's payslips.
    try:
        payroll.list_payslips(school_id=None, db=db, current_user=staff)
        assert False
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403
    # But can read their own by id.
    assert payroll.get_payslip(record_id=slip.id, db=db, current_user=staff).id == slip.id
