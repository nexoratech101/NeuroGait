import enum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.db_types import GUID as UUID
from app.db_types import PortableJSON as JSONB


def uuid_pk():
    return Column(UUID, primary_key=True, default=uuid.uuid4)


class UserRole(str, enum.Enum):
    admin = "admin"
    physician = "physician"
    researcher = "researcher"


class SessionStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    complete = "complete"
    failed = "failed"


class SensorPosition(str, enum.Enum):
    ankle_l = "ankle_l"
    ankle_r = "ankle_r"
    thigh_l = "thigh_l"
    thigh_r = "thigh_r"
    hip = "hip"
    unknown = "unknown"


class User(Base):
    __tablename__ = "users"

    user_id = uuid_pk()
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.researcher)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)


class Patient(Base):
    __tablename__ = "patients"

    patient_id = uuid_pk()
    study_id = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    mobile_number = Column(String, nullable=True)
    dob = Column(Date, nullable=True)
    sex = Column(String, nullable=True)
    enrollment_date = Column(Date, nullable=True)
    treating_physician_id = Column(UUID, ForeignKey("users.user_id"), nullable=True)

    ms_phenotype = Column(String, nullable=True)
    year_of_diagnosis = Column(Integer, nullable=True)
    mobility_status = Column(String, nullable=True)
    assistive_device = Column(String, nullable=True)
    edss_score = Column(Float, nullable=True)
    edss_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    # Placeholder field only -- REB/consent workflow enforcement is Future work.
    consent_recorded = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sessions = relationship("GaitSession", back_populates="patient")


class Device(Base):
    __tablename__ = "devices"

    device_id = uuid_pk()
    device_serial = Column(String, unique=True, nullable=False)
    model = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)
    sensor_model = Column(String, nullable=True)
    default_position = Column(Enum(SensorPosition), nullable=True)
    last_calibration_date = Column(Date, nullable=True)


class GaitSession(Base):
    __tablename__ = "sessions"

    session_id = uuid_pk()
    # Nullable: an uploaded session with no filename metadata and no manual
    # association yet has no patient until POST /sessions/{id}/associate runs.
    patient_id = Column(UUID, ForeignKey("patients.patient_id"), nullable=True)
    assessment_date = Column(DateTime(timezone=True), server_default=func.now())
    test_type = Column(String, nullable=True)
    conditions = Column(JSONB, nullable=True)
    clinician_id = Column(UUID, ForeignKey("users.user_id"), nullable=True)
    processing_version = Column(String, nullable=True)
    status = Column(Enum(SessionStatus), nullable=False, default=SessionStatus.uploaded)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="sessions")
    recordings = relationship("SensorRecording", back_populates="session")
    analysis = relationship("GaitAnalysis", back_populates="session", uselist=False)
    notes = relationship("ClinicalNote", back_populates="session")
    reports = relationship("Report", back_populates="session")


class SensorRecording(Base):
    __tablename__ = "sensor_recordings"

    recording_id = uuid_pk()
    session_id = Column(UUID, ForeignKey("sessions.session_id"), nullable=False)
    device_id = Column(UUID, ForeignKey("devices.device_id"), nullable=True)
    position_claimed = Column(Enum(SensorPosition), nullable=True)
    position_verified = Column(Boolean, nullable=True)
    position_confidence = Column(Float, nullable=True)
    raw_file_path = Column(String, nullable=False)
    raw_file_hash = Column(String, nullable=False)
    sampling_rate_hz_estimated = Column(Float, nullable=True)
    n_samples = Column(Integer, nullable=True)
    duration_s = Column(Float, nullable=True)
    gap_count = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("GaitSession", back_populates="recordings")


class GaitAnalysis(Base):
    __tablename__ = "gait_analysis"

    analysis_id = uuid_pk()
    session_id = Column(UUID, ForeignKey("sessions.session_id"), nullable=False)
    algorithm_version = Column(String, nullable=False)

    walking_duration_s = Column(Float, nullable=True)
    n_walking_bouts = Column(Integer, nullable=True)

    cadence_spm = Column(Float, nullable=True)
    cadence_status = Column(String, nullable=True)  # measured / estimated / derived

    step_time_s = Column(Float, nullable=True)
    step_time_cv_pct = Column(Float, nullable=True)

    stride_time_s = Column(Float, nullable=True)
    stride_time_cv_pct = Column(Float, nullable=True)

    gait_regularity_index = Column(Float, nullable=True)

    speed_mps = Column(Float, nullable=True)
    speed_status = Column(String, nullable=True)  # always 'estimated' in Phase 1

    # Future placeholders -- present in schema, unused/null in Phase 1.
    gait_asymmetry_pct = Column(Float, nullable=True)
    turning_metrics = Column(JSONB, nullable=True)
    fatigue_metrics = Column(JSONB, nullable=True)
    movement_smoothness = Column(Float, nullable=True)

    quality_score = Column(Float, nullable=True)
    quality_flags = Column(JSONB, nullable=True)

    computed_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("GaitSession", back_populates="analysis")


class ClinicalNote(Base):
    __tablename__ = "clinical_notes"

    note_id = uuid_pk()
    session_id = Column(UUID, ForeignKey("sessions.session_id"), nullable=False)
    clinician_id = Column(UUID, ForeignKey("users.user_id"), nullable=True)
    note_text = Column(Text, nullable=True)
    fatigue_reported = Column(Boolean, nullable=True)
    pain_reported = Column(Boolean, nullable=True)
    relapse_reported = Column(Boolean, nullable=True)
    medication_change = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("GaitSession", back_populates="notes")


class Report(Base):
    __tablename__ = "reports"

    report_id = uuid_pk()
    session_id = Column(UUID, ForeignKey("sessions.session_id"), nullable=False)
    report_file_path = Column(String, nullable=False)
    report_version = Column(String, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    generated_by = Column(UUID, ForeignKey("users.user_id"), nullable=True)

    session = relationship("GaitSession", back_populates="reports")


class AuditLog(Base):
    __tablename__ = "audit_log"

    log_id = uuid_pk()
    user_id = Column(UUID, ForeignKey("users.user_id"), nullable=True)
    action = Column(String, nullable=False)
    target_table = Column(String, nullable=True)
    target_id = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String, nullable=True)
