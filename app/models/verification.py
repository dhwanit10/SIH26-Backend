from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class VerificationEntry(Base):
    __tablename__ = "verification_entries"

    id = Column(Integer, primary_key=True, index=True)
    date_time_recorded = Column(DateTime, default=datetime.utcnow)
    # Foreign Keys
    doc_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    officer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)
    # Relationships
    document = relationship("Document", back_populates="verifications")
    officer = relationship("User", foreign_keys=[officer_id], back_populates="verifications")
    risk_entries = relationship("Risk", back_populates="verification")
    session = relationship("Session", back_populates="verifications")