from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine, Base
from backend.models import ReferenceData

# Comprehensive List of Levels (Francophone Africa Focus + Anglophone equivalents)
EDUCATION_LEVELS = [
    # Maternelle (Nursery)
    {"key": "MAT_PS", "value": {"fr": "Petite Section", "en": "Nursery 1"}, "order": 10},
    {"key": "MAT_MS", "value": {"fr": "Moyenne Section", "en": "Nursery 2"}, "order": 20},
    {"key": "MAT_GS", "value": {"fr": "Grande Section", "en": "Kindergarten"}, "order": 30},
    
    # Primaire (Primary)
    {"key": "PRIM_CP", "value": {"fr": "CP (Cours Préparatoire)", "en": "Grade 1"}, "order": 40},
    {"key": "PRIM_CE1", "value": {"fr": "CE1 (Cours Élémentaire 1)", "en": "Grade 2"}, "order": 50},
    {"key": "PRIM_CE2", "value": {"fr": "CE2 (Cours Élémentaire 2)", "en": "Grade 3"}, "order": 60},
    {"key": "PRIM_CM1", "value": {"fr": "CM1 (Cours Moyen 1)", "en": "Grade 4"}, "order": 70},
    {"key": "PRIM_CM2", "value": {"fr": "CM2 (Cours Moyen 2)", "en": "Grade 5"}, "order": 80},
    
    # Collège (Middle School/Junior Secondary)
    {"key": "SEC_6EME", "value": {"fr": "6ème", "en": "Grade 6"}, "order": 90},
    {"key": "SEC_5EME", "value": {"fr": "5ème", "en": "Grade 7"}, "order": 100},
    {"key": "SEC_4EME", "value": {"fr": "4ème", "en": "Grade 8"}, "order": 110},
    {"key": "SEC_3EME", "value": {"fr": "3ème", "en": "Grade 9"}, "order": 120},
    
    # Lycée (High School/Senior Secondary)
    {"key": "LYC_2NDE", "value": {"fr": "2nde (Seconde)", "en": "Grade 10"}, "order": 130},
    {"key": "LYC_1ERE", "value": {"fr": "1ère (Première)", "en": "Grade 11"}, "order": 140},
    {"key": "LYC_TERM", "value": {"fr": "Terminale", "en": "Grade 12"}, "order": 150},
    
    # Supérieur (University/Professional)
    {"key": "UNIV_L1", "value": {"fr": "Licence 1", "en": "Bachelor Year 1"}, "order": 160},
    {"key": "UNIV_L2", "value": {"fr": "Licence 2", "en": "Bachelor Year 2"}, "order": 170},
    {"key": "UNIV_L3", "value": {"fr": "Licence 3", "en": "Bachelor Year 3"}, "order": 180},
    {"key": "UNIV_M1", "value": {"fr": "Master 1", "en": "Master Year 1"}, "order": 190},
    {"key": "UNIV_M2", "value": {"fr": "Master 2", "en": "Master Year 2"}, "order": 200},
    {"key": "UNIV_DOC", "value": {"fr": "Doctorat", "en": "PhD"}, "order": 210},
    
    # Professional/Technique
    {"key": "PRO_CAP", "value": {"fr": "CAP", "en": "Vocational Certificate"}, "order": 135},
    {"key": "PRO_BEP", "value": {"fr": "BEP", "en": "Vocational Diploma"}, "order": 136},
    {"key": "PRO_BTS", "value": {"fr": "BTS", "en": "Higher Technician Certificate"}, "order": 165},
]

def seed_reference_data():
    db = SessionLocal()
    try:
        # Create Tables first if they don't exist (ensures ReferenceData table exists)
        Base.metadata.create_all(bind=engine)
        
        print("Seeding Education Levels...")
        count = 0
        for level in EDUCATION_LEVELS:
            # Check if exists (Global default, school_id=None)
            exists = db.query(ReferenceData).filter(
                ReferenceData.category == "EDUCATION_LEVEL",
                ReferenceData.key == level["key"],
                ReferenceData.school_id == None
            ).first()
            
            if not exists:
                new_ref = ReferenceData(
                    category="EDUCATION_LEVEL",
                    key=level["key"],
                    value=level["value"], # SQLAlchemy JSON handles dict -> json
                    order=level["order"],
                    school_id=None # Global
                )
                db.add(new_ref)
                count += 1
        
        db.commit()
        print(f"✅ seeded {count} new education levels.")
        
    except Exception as e:
        print(f"❌ Seeding Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_reference_data()
