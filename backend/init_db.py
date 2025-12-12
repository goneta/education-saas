from backend.database import engine, Base
from backend import models

print("Creating all tables in database...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully.")
