from app.core.database import engine, Base
from app.models import (
    User, Document, 
    VerificationEntry, Risk, System, Session
)

def createTables():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")