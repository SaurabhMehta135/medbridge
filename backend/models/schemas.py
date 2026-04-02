"""
MedBridge — Pydantic Schemas for request validation and response serialization.
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class UserRegister(BaseModel):
    email: str
    password: str = Field(min_length=6)
    full_name: str
    role: str = Field(pattern="^(patient|doctor)$")
    phone_number: str = Field(min_length=10, max_length=15)

    # Optional profile fields sent during registration
    date_of_birth: Optional[date] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    specialty: Optional[str] = None
    license_number: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class PasswordReset(BaseModel):
    email: str
    new_password: str = Field(min_length=6)


class PhoneLogin(BaseModel):
    phone_number: str
    password: str


class OTPRequest(BaseModel):
    phone_number: str


class OTPVerify(BaseModel):
    phone_number: str
    otp: str
    new_password: str = Field(min_length=6)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    specialty: Optional[str] = None
    license_number: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    specialty: Optional[str] = None
    license_number: Optional[str] = None


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

class DocumentOut(BaseModel):
    id: int
    patient_id: int
    original_filename: str
    file_size: int
    doc_type: str
    specialty: Optional[str] = None
    patient_summary: Optional[str] = None
    clinical_summary: Optional[str] = None
    is_processed: bool
    uploaded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentDetail(DocumentOut):
    content_text: Optional[str] = None


# ---------------------------------------------------------------------------
# Access Codes
# ---------------------------------------------------------------------------

class AccessCodeCreate(BaseModel):
    expires_in_hours: int = Field(default=24, ge=1, le=720)  # 1h to 30 days


class AccessCodeOut(BaseModel):
    id: int
    code: str
    patient_id: int
    doctor_id: Optional[int] = None
    expires_at: datetime
    is_revoked: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AccessCodeVerify(BaseModel):
    code: str


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    patient_id: Optional[int] = None  # doctor specifies which patient


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

class AlertOut(BaseModel):
    alert_type: str   # "drug_interaction", "allergy", "duplicate_med"
    severity: str     # "info", "warning", "critical"
    title: str
    description: str
    related_drugs: List[str] = []

# ---------------------------------------------------------------------------
# FollowUps
# ---------------------------------------------------------------------------

class FollowUpBase(BaseModel):
    follow_up_type: str
    description: str
    timeframe_text: Optional[str] = None
    due_date: Optional[date] = None
    urgency: Optional[str] = "routine"
    specialty: Optional[str] = None
    status: Optional[str] = "pending"
    notes: Optional[str] = None

class FollowUpCreate(FollowUpBase):
    pass

class FollowUpOut(FollowUpBase):
    id: int
    patient_id: int
    document_id: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class FollowUpUpdate(BaseModel):
    status: Optional[str] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None
