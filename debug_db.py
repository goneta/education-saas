from backend.database import engine, Base, SessionLocal
from backend import models, security
from sqlalchemy.exc import IntegrityError

def debug_setup():
    print("Creating tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created.")
    except Exception as e:
        print(f"Error creating tables: {e}")
        return

    db = SessionLocal()
    try:
        print("Attempting to create School...")
        school = models.School(
            name="Test School",
            domain_prefix="testschool",
            school_type=models.SchoolType.GENERAL
        )
        db.add(school)
        db.commit()
        db.refresh(school)
        print(f"School created: {school.id}")
        
        print("Attempting to create User...")
        user = models.User(
            email="test@test.com",
            hashed_password="hash",
            full_name="Test User",
            role=models.UserRole.SCHOOL_ADMIN,
            school_id=school.id
        )
        db.add(user)
        db.commit()
        print("User created.")
    except Exception as e:
        print(f"Transaction failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_setup()
