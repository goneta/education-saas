
from backend.database import engine
from sqlalchemy import inspect
import os

def check():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables: {tables}")
    if "student_education_history" in tables:
        print("SUCCESS: student_education_history table exists.")
    else:
        print("FAILURE: student_education_history table NOT found.")

if __name__ == "__main__":
    check()
