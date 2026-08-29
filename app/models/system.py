from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Date
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
from datetime import datetime, date

class SystemStatus(enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DOWN = "down"

class System(Base):
    __tablename__ = "systems"

    id = Column(Integer, primary_key=True, index=True)
    system_name = Column(String(100), unique=True, nullable=False)
    status = Column(Enum(SystemStatus), default=SystemStatus.OFFLINE)
    
    # Foreign Keys
    primary_owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    primary_owner = relationship("User", back_populates="owned_systems")
    sessions = relationship("Session", back_populates="system")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    no_of_cases = Column(Integer, default=0)
    
    # Foreign Keys
    officer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    system_id = Column(Integer, ForeignKey("systems.id"), nullable=False)

    # Relationships
    officer = relationship("User", back_populates="sessions")
    system = relationship("System", back_populates="sessions")
    verifications = relationship("VerificationEntry", back_populates="session")
