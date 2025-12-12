from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
from backend import models, security
from backend.models import UserRole, SchoolType, DayOfWeek, AttendanceStatus, AssessmentType
from datetime import datetime, date, time, timedelta

def create_test_data():
    db = SessionLocal()
    try:
        # 1. Create School
        school = db.query(models.School).filter(models.School.domain_prefix == "demo").first()
        if not school:
            school = models.School(
                name="Demo School",
                domain_prefix="demo",
                school_type=SchoolType.GENERAL,
                email="contact@demo.school",
                subscription_plan="premium"
            )
            db.add(school)
            db.commit()
            db.refresh(school)
        print(f"School: {school.name}")

        # 2. Create Admin User
        admin = db.query(models.User).filter(models.User.email == "admin@demo.school").first()
        if not admin:
            admin = models.User(
                email="admin@demo.school",
                hashed_password=security.get_password_hash("admin123"),
                full_name="Admin User",
                role=UserRole.SCHOOL_ADMIN,
                school_id=school.id
            )
            db.add(admin)
            db.commit()
            print("Created Admin User: admin@demo.school / admin123")
        else:
            print("Admin User already exists")

        # 3. Create Students (for stats)
        # Check count
        count = db.query(models.StudentProfile).filter(models.StudentProfile.user.has(school_id=school.id)).count()
        if count < 5:
            for i in range(5):
                email = f"student{i}@demo.school"
                if not db.query(models.User).filter(models.User.email == email).first():
                    student_user = models.User(
                        email=email,
                        hashed_password=security.get_password_hash("student123"),
                        full_name=f"Student {i}",
                        role=UserRole.STUDENT,
                        school_id=school.id
                    )
                    db.add(student_user)
                    db.flush()
                    
                    profile = models.StudentProfile(
                        user_id=student_user.id,
                        registration_number=f"STU{i:04d}",
                        date_of_birth=datetime(2010, 1, 1),
                        gender="M"
                    )
                    db.add(profile)
            db.commit()
            print("Created 5 dummy students")

        # 4. Create Timetable for Today (Upcoming Classes)
        today_name = date.today().strftime('%A').lower() # e.g. "thursday"
        # Check if we have classes today
        timetables_count = db.query(models.Timetable).join(models.Class).filter(
            models.Timetable.day_of_week == today_name,
            models.Class.school_id == school.id
        ).count()
        
        if timetables_count == 0:
            # Need a class and subject
            cls = db.query(models.Class).filter(models.Class.school_id == school.id).first()
            if not cls:
                cls = models.Class(name="Grade 10 A", level="10", school_id=school.id)
                db.add(cls)
                db.commit()
                db.refresh(cls)
                
            subj = db.query(models.Subject).filter(models.Subject.school_id == school.id).first()
            if not subj:
                subj = models.Subject(name="Mathematics", code="MATH", school_id=school.id)
                db.add(subj)
                db.commit()
                db.refresh(subj)
            
            # Create 3 slots
            for h in [8, 10, 14]:
                tt = models.Timetable(
                    day_of_week=today_name, # Mapped correctly? MONDAY="monday"
                    start_time=time(h, 0),
                    end_time=time(h+1, 0),
                    class_id=cls.id,
                    subject_id=subj.id,
                    # teacher_id can be null or admin
                )
                db.add(tt)
            db.commit()
            print(f"Created 3 timetable slots for {today_name}")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()
