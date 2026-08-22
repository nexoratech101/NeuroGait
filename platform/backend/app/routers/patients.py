import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, record_audit
from app.models import GaitSession, Patient, User
from app.schemas import PatientCreate, PatientOut, PatientUpdate

router = APIRouter(prefix="/patients", tags=["patients"])


def _new_study_id(db: Session) -> str:
    count = db.query(Patient).count()
    return f"STU-{count + 1:04d}"


@router.get("", response_model=List[PatientOut])
def list_patients(q: str = "", db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Patient)
    if q:
        query = query.filter(Patient.full_name.ilike(f"%{q}%"))
    return query.order_by(Patient.created_at.desc()).all()


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    study_id = payload.study_id or _new_study_id(db)
    patient = Patient(**{**payload.model_dump(exclude={"study_id"}), "study_id": study_id})
    db.add(patient)
    db.commit()
    db.refresh(patient)
    record_audit(db, user, "create_patient", "patients", patient.patient_id)
    return patient


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    patient = db.query(Patient).get(patient_id)
    if not patient:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found")
    return patient


@router.patch("/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: uuid.UUID, payload: PatientUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    patient = db.query(Patient).get(patient_id)
    if not patient:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    record_audit(db, user, "update_patient", "patients", patient.patient_id)
    return patient


@router.get("/{patient_id}/sessions")
def list_patient_sessions(patient_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    patient = db.query(Patient).get(patient_id)
    if not patient:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found")
    sessions = (
        db.query(GaitSession)
        .filter(GaitSession.patient_id == patient_id)
        .order_by(GaitSession.assessment_date.asc())
        .all()
    )
    return [
        {
            "session_id": str(s.session_id),
            "assessment_date": s.assessment_date.isoformat() if s.assessment_date else None,
            "test_type": s.test_type,
            "status": s.status.value,
        }
        for s in sessions
    ]
