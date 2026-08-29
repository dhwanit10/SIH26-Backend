from sqlalchemy import Column, Integer, String, Date, Enum, DateTime, LargeBinary
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
from datetime import datetime

class UserStatus(enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"

class UserType(enum.Enum):
    OFFICER = "officer"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=False)
    dob = Column(Date, nullable=False)
    gender = Column(String(10), nullable=False)
    aadhar_no = Column(String(12), unique=True, nullable=False)
    phone = Column(String(15), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    face_image = Column(LargeBinary, nullable=True)  # Store image as bytes
    user_type = Column(Enum(UserType), default=UserType.OFFICER, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.OFFLINE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="user")
    verifications = relationship("VerificationEntry", foreign_keys="VerificationEntry.officer_id", back_populates="officer")
    risk_entries = relationship("Risk", foreign_keys="Risk.officer_id", back_populates="officer")
    risk_verifications = relationship("Risk", foreign_keys="Risk.verifier_admin_id", back_populates="verifier_admin")
    owned_systems = relationship("System", back_populates="primary_owner")
    sessions = relationship("Session", back_populates="officer")