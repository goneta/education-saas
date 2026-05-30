"""
Create a simple test admin user for login testing
"""
import sys
sys.path.append('.')

from backend.database import SessionLocal
from backend.models import User, School, UserRole
from backend.security import get_password_hash

def create_test_admin():
    db = SessionLocal()
    
    try:
        # Check if test school exists
        test_school = db.query(School).filter(School.domain_prefix == "testschool").first()
        
        if not test_school:
            # Create test school
            test_school = School(
                name="Test School",
                domain_prefix="testschool",
                school_type="general",
                address="123 Test Street"
            )
            db.add(test_school)
            db.commit()
            db.refresh(test_school)
            print(f"✅ Created test school: {test_school.name}")
        else:
            print(f"ℹ️  Test school already exists: {test_school.name}")
        
        # Check if test admin exists
        test_admin = db.query(User).filter(User.email == "admin@test.com").first()
        
        if test_admin:
            print(f"ℹ️  Test admin already exists: {test_admin.email}")
            print(f"   Email: admin@test.com")
            print(f"   Password: admin123")
            return
        
        # Create test admin user
        hashed_password = get_password_hash("admin123")
        test_admin = User(
            email="admin@test.com",
            hashed_password=hashed_password,
            full_name="Test Admin",
            role=UserRole.SCHOOL_ADMIN,
            school_id=test_school.id,
            is_active=True
        )
        db.add(test_admin)
        db.commit()
        db.refresh(test_admin)
        
        print("✅ Test admin user created successfully!")
        print("\n" + "="*50)
        print("LOGIN CREDENTIALS:")
        print("="*50)
        print(f"Email:    admin@test.com")
        print(f"Password: admin123")
        print("="*50)
        
    except Exception as e:
        print(f"❌ Error creating test admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_admin()
