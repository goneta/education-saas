"""Seed a small, idempotent demo dataset for local dashboard verification."""

import logging
from datetime import date, datetime, time

from backend import models, security
from backend.database import SessionLocal
from backend.models import SchoolType, UserRole

logger = logging.getLogger(__name__)


def create_test_data() -> None:
    """Create deterministic demo data for local manual testing."""
    db = SessionLocal()
    try:
        school = db.query(models.School).filter(models.School.domain_prefix == "demo").first()
        if not school:
            school = models.School(
                name="Demo School",
                domain_prefix="demo",
                school_type=SchoolType.GENERAL,
                email="contact@demo.school",
                subscription_plan="premium",
            )
            db.add(school)
            db.commit()
            db.refresh(school)
        logger.info("Demo school ready: %s", school.name)

        admin = db.query(models.User).filter(models.User.email == "admin@demo.school").first()
        if not admin:
            admin = models.User(
                email="admin@demo.school",
                hashed_password=security.get_password_hash("admin123"),
                full_name="Admin User",
                role=UserRole.SCHOOL_ADMIN,
                school_id=school.id,
            )
            db.add(admin)
            db.commit()
            logger.info("Demo admin user created: admin@demo.school")
        else:
            logger.info("Demo admin user already exists")

        student_count = db.query(models.StudentProfile).filter(
            models.StudentProfile.user.has(school_id=school.id)
        ).count()
        if student_count < 5:
            created_students = 0
            for i in range(5):
                email = f"student{i}@demo.school"
                if not db.query(models.User).filter(models.User.email == email).first():
                    student_user = models.User(
                        email=email,
                        hashed_password=security.get_password_hash("student123"),
                        full_name=f"Student {i}",
                        role=UserRole.STUDENT,
                        school_id=school.id,
                    )
                    db.add(student_user)
                    db.flush()

                    profile = models.StudentProfile(
                        user_id=student_user.id,
                        registration_number=f"STU{i:04d}",
                        date_of_birth=datetime(2010, 1, 1),
                        gender="M",
                    )
                    db.add(profile)
                    created_students += 1
            db.commit()
            logger.info("Demo students created: %s", created_students)

        today_name = date.today().strftime("%A").lower()
        timetables_count = db.query(models.Timetable).join(models.Class).filter(
            models.Timetable.day_of_week == today_name,
            models.Class.school_id == school.id,
        ).count()

        if timetables_count == 0:
            cls = db.query(models.Class).filter(models.Class.school_id == school.id).first()
            if not cls:
                cls = models.Class(name="Grade 10 A", level="10", school_id=school.id)
                db.add(cls)
                db.commit()
                db.refresh(cls)

            subject = db.query(models.Subject).filter(models.Subject.school_id == school.id).first()
            if not subject:
                subject = models.Subject(name="Mathematics", code="MATH", school_id=school.id)
                db.add(subject)
                db.commit()
                db.refresh(subject)

            for hour in [8, 10, 14]:
                timetable = models.Timetable(
                    day_of_week=today_name,
                    start_time=time(hour, 0),
                    end_time=time(hour + 1, 0),
                    class_id=cls.id,
                    subject_id=subject.id,
                )
                db.add(timetable)
            db.commit()
            logger.info("Demo timetable slots created for %s", today_name)

    except Exception:
        logger.exception("Unable to create demo dashboard data")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    create_test_data()
