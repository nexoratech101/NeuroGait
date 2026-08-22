from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str


class PatientCreate(BaseModel):
    full_name: str
    study_id: Optional[str] = None
    mobile_number: Optional[str] = None
    dob: Optional[date] = None
    sex: Optional[str] = None
    enrollment_date: Optional[date] = None
    ms_phenotype: Optional[str] = None
    year_of_diagnosis: Optional[int] = None
    mobility_status: Optional[str] = None
    assistive_device: Optional[str] = None
    edss_score: Optional[float] = None
    edss_date: Optional[date] = None
    notes: Optional[str] = None
    consent_recorded: bool = False


class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    mobile_number: Optional[str] = None
    dob: Optional[date] = None
    sex: Optional[str] = None
    ms_phenotype: Optional[str] = None
    year_of_diagnosis: Optional[int] = None
    mobility_status: Optional[str] = None
    assistive_device: Optional[str] = None
    edss_score: Optional[float] = None
    edss_date: Optional[date] = None
    notes: Optional[str] = None
    consent_recorded: Optional[bool] = None


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    patient_id: UUID
    study_id: str
    full_name: str
    mobile_number: Optional[str] = None
    dob: Optional[date] = None
    sex: Optional[str] = None
    enrollment_date: Optional[date] = None
    ms_phenotype: Optional[str] = None
    year_of_diagnosis: Optional[int] = None
    mobility_status: Optional[str] = None
    assistive_device: Optional[str] = None
    edss_score: Optional[float] = None
    edss_date: Optional[date] = None
    notes: Optional[str] = None
    consent_recorded: bool
    created_at: datetime


class AssociateSessionRequest(BaseModel):
    patient_id: Optional[UUID] = None
    new_patient: Optional[PatientCreate] = None


class NoteCreate(BaseModel):
    note_text: Optional[str] = None
    fatigue_reported: Optional[bool] = None
    pain_reported: Optional[bool] = None
    relapse_reported: Optional[bool] = None
    medication_change: Optional[bool] = None


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    note_id: UUID
    session_id: UUID
    note_text: Optional[str] = None
    fatigue_reported: Optional[bool] = None
    pain_reported: Optional[bool] = None
    relapse_reported: Optional[bool] = None
    medication_change: Optional[bool] = None
    created_at: datetime


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: UUID
    patient_id: UUID
    assessment_date: datetime
    test_type: Optional[str] = None
    conditions: Optional[Any] = None
    processing_version: Optional[str] = None
    status: str
    created_at: datetime
