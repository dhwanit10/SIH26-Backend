from sqlalchemy import Column, Integer, String, Date, ForeignKey, LargeBinary, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class DocumentTypeEnum(enum.Enum):
    PASSPORT = "passport"
    AADHAR = "aadhar"
    DRIVING_LICENSE = "driving_license"
    UNKNOWN = "unknown"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(200), nullable=False)
    doc_number = Column(String(50), unique=True, nullable=False, index=True)
    doc_type = Column(Enum(DocumentTypeEnum), nullable=False)
    gender = Column(String(10), nullable=True)
    nationality = Column(String(100), nullable=True)
    doc_photo = Column(LargeBinary, nullable=True)
    dob = Column(Date, nullable=True)
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    mrz_no = Column(String(100), nullable=True)
    person_image = Column(LargeBinary, nullable=True)
    address = Column(String(500), nullable=True)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="documents")
    verifications = relationship("VerificationEntry", back_populates="document")
    risk_entries = relationship("Risk", back_populates="document")