"""
MedBridge — SQLAlchemy Database Models & Session Setup

Tables:
  - users: patients and doctors
  - documents: uploaded medical PDFs
  - access_codes: time-scoped sharing codes between patient → doctor
"""

import os
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey, create_engine, text
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/medbridge.db")

# Fail fast on hosted Postgres so Render shows a real DB error instead of timing out.
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
else:
    connect_args = {"connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10"))}
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_recycle=300,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # "patient" or "doctor"
    phone_number = Column(String(20), nullable=True, index=True)

    # Patient-specific profile fields
    date_of_birth = Column(Date, nullable=True)
    blood_type = Column(String(10), nullable=True)
    allergies = Column(Text, nullable=True)          # comma-separated
    medications = Column(Text, nullable=True)        # comma-separated current meds
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(50), nullable=True)

    # Doctor-specific profile fields
    specialty = Column(String(255), nullable=True)
    license_number = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="patient", foreign_keys="Document.patient_id")
    access_codes_given = relationship("AccessCode", back_populates="patient", foreign_keys="AccessCode.patient_id")
    access_codes_received = relationship("AccessCode", back_populates="doctor", foreign_keys="AccessCode.doctor_id")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)          # stored filename (uuid)
    original_filename = Column(String(255), nullable=False)  # user-facing name
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    content_text = Column(Text, nullable=True)               # extracted full text
    patient_summary = Column(Text, nullable=True)            # LLM generated plain English summary
    clinical_summary = Column(Text, nullable=True)           # LLM generated doctor-facing summary
    doc_type = Column(String(50), default="general")         # lab_report, prescription, discharge_summary, etc.
    specialty = Column(String(100), nullable=True)            # medical specialty tag
    is_processed = Column(Boolean, default=False)            # True after RAG embedding
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient = relationship("User", back_populates="documents", foreign_keys=[patient_id])
    uploader = relationship("User", foreign_keys=[uploaded_by])


class AccessCode(Base):
    __tablename__ = "access_codes"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)   # set when doctor claims
    code = Column(String(20), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient = relationship("User", back_populates="access_codes_given", foreign_keys=[patient_id])
    doctor = relationship("User", back_populates="access_codes_received", foreign_keys=[doctor_id])


# ---------------------------------------------------------------------------
# FollowUps
# ---------------------------------------------------------------------------

class FollowUp(Base):
    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True, index=True)
    
    follow_up_type = Column(String(50), nullable=False) # appointment, lab_test, referral, imaging, etc.
    description = Column(Text, nullable=False)
    timeframe_text = Column(String(255), nullable=True)
    due_date = Column(Date, nullable=True)
    urgency = Column(String(20), default="routine") # routine, soon, urgent
    specialty = Column(String(100), nullable=True)
    
    status = Column(String(20), default="pending") # pending, completed, overdue
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    patient = relationship("User", foreign_keys=[patient_id])
    document = relationship("Document", foreign_keys=[document_id])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def init_db():
    """Verify connectivity and create all tables if they don't exist."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
