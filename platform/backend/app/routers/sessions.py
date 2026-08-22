import json
import uuid
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, record_audit
from app.models import (
    ClinicalNote,
    GaitAnalysis,
    GaitSession,
    Patient,
    Report,
    SensorPosition,
    SensorRecording,
    SessionStatus,
    User,
)
from app.pipeline.file_validator import validate_file
from app.pipeline.metadata_extractor import extract_metadata
from app.pipeline.patient_association import resolve_association
from app.pipeline.qc import run_qc
from app.pipeline.trend import TrendPoint, build_trend_series
from app.pipeline_service import run_session_processing
from app.report_generator import generate_report_pdf
from app.schemas import AssociateSessionRequest, NoteCreate, NoteOut
from app.storage import save_raw_file

import pandas as pd

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _position_enum(value: Optional[str]) -> SensorPosition:
    if not value:
        return SensorPosition.unknown
    try:
        return SensorPosition(value)
    except ValueError:
        return SensorPosition.unknown


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_session(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    test_type: Optional[str] = Form(None),
    conditions: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not (1 <= len(files) <= 3):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Upload requires 1 to 3 sensor files")

    parsed_conditions = None
    if conditions:
        try:
            parsed_conditions = json.loads(conditions)
        except json.JSONDecodeError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "conditions must be valid JSON")

    session = GaitSession(
        patient_id=None,
        test_type=test_type,
        conditions=parsed_conditions,
        clinician_id=user.user_id,
        status=SessionStatus.uploaded,
    )
    db.add(session)
    db.flush()

    known_study_ids = [row[0] for row in db.query(Patient.study_id).all()]

    file_reports = []
    matched_patient_id = None
    any_metadata = False

    for upload in files:
        content = await upload.read()
        raw_path, file_hash = save_raw_file(str(session.session_id), upload.filename, content)

        validation = validate_file(raw_path)
        metadata = extract_metadata(upload.filename)
        association = resolve_association(metadata, known_study_ids)

        qc = None
        if validation.valid:
            df = pd.read_csv(raw_path)
            qc = run_qc(df)

        recording = SensorRecording(
            session_id=session.session_id,
            position_claimed=_position_enum(metadata.position),
            raw_file_path=raw_path,
            raw_file_hash=file_hash,
            sampling_rate_hz_estimated=qc.sampling_rate_hz_estimated if qc else None,
            n_samples=qc.n_samples if qc else validation.n_rows,
            duration_s=qc.duration_s if qc else None,
            gap_count=qc.gap_count if qc else None,
        )
        db.add(recording)

        if metadata.has_metadata:
            any_metadata = True
        if association.matched_study_id:
            patient = db.query(Patient).filter(Patient.study_id == association.matched_study_id).first()
            if patient:
                matched_patient_id = patient.patient_id

        file_reports.append({
            "filename": upload.filename,
            "valid": validation.valid,
            "errors": validation.errors,
            "metadata_found": metadata.has_metadata,
            "detected_position": metadata.position,
            "detected_patient_study_id": metadata.patient_study_id,
            "association_reason": association.reason,
        })

    needs_association = matched_patient_id is None
    if matched_patient_id:
        session.patient_id = matched_patient_id

    db.commit()
    db.refresh(session)
    record_audit(db, user, "upload_session", "sessions", session.session_id)

    if not needs_association:
        background_tasks.add_task(run_session_processing, str(session.session_id))

    return {
        "session_id": str(session.session_id),
        "needs_association": needs_association,
        "legacy_no_metadata": not any_metadata,
        "files": file_reports,
    }


@router.post("/{session_id}/associate")
def associate_session(
    session_id: uuid.UUID,
    payload: AssociateSessionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = db.query(GaitSession).get(session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")

    if payload.patient_id:
        patient = db.query(Patient).get(payload.patient_id)
        if not patient:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found")
        session.patient_id = patient.patient_id
    elif payload.new_patient:
        count = db.query(Patient).count()
        study_id = payload.new_patient.study_id or f"STU-{count + 1:04d}"
        patient = Patient(**{**payload.new_patient.model_dump(exclude={"study_id"}), "study_id": study_id})
        db.add(patient)
        db.flush()
        session.patient_id = patient.patient_id
    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Provide patient_id or new_patient")

    db.commit()
    record_audit(db, user, "associate_session", "sessions", session.session_id)

    background_tasks.add_task(run_session_processing, str(session.session_id))
    return {"session_id": str(session.session_id), "patient_id": str(session.patient_id), "status": "processing"}


@router.get("/{session_id}")
def get_session(session_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = db.query(GaitSession).get(session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    recordings = db.query(SensorRecording).filter(SensorRecording.session_id == session_id).all()
    return {
        "session_id": str(session.session_id),
        "patient_id": str(session.patient_id) if session.patient_id else None,
        "assessment_date": session.assessment_date.isoformat() if session.assessment_date else None,
        "test_type": session.test_type,
        "conditions": session.conditions,
        "status": session.status.value,
        "processing_version": session.processing_version,
        "recordings": [
            {
                "recording_id": str(r.recording_id),
                "position_claimed": r.position_claimed.value if r.position_claimed else None,
                "position_verified": r.position_verified,
                "position_confidence": r.position_confidence,
                "sampling_rate_hz_estimated": r.sampling_rate_hz_estimated,
                "n_samples": r.n_samples,
                "duration_s": r.duration_s,
                "gap_count": r.gap_count,
                "raw_file_hash": r.raw_file_hash,
            }
            for r in recordings
        ],
    }


@router.get("/{session_id}/status")
def get_session_status(session_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = db.query(GaitSession).get(session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    return {"session_id": str(session.session_id), "status": session.status.value}


def _tagged(value, status_str, unit):
    return {"value": value, "status": status_str, "unit": unit}


@router.get("/{session_id}/analysis")
def get_analysis(session_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = db.query(GaitSession).get(session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    analysis = db.query(GaitAnalysis).filter(GaitAnalysis.session_id == session_id).first()
    if not analysis:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not yet available")

    return {
        "session_id": str(session_id),
        "algorithm_version": analysis.algorithm_version,
        "walking_duration_s": analysis.walking_duration_s,
        "n_walking_bouts": analysis.n_walking_bouts,
        "metrics": {
            "cadence_spm": _tagged(analysis.cadence_spm, analysis.cadence_status, "steps/min"),
            "step_time_s": _tagged(analysis.step_time_s, "measured", "s"),
            "step_time_cv_pct": _tagged(analysis.step_time_cv_pct, "measured", "%"),
            "stride_time_s": _tagged(analysis.stride_time_s, "measured", "s"),
            "stride_time_cv_pct": _tagged(analysis.stride_time_cv_pct, "measured", "%"),
            "gait_regularity_index": _tagged(analysis.gait_regularity_index, "derived", "unitless"),
            "speed_mps": _tagged(analysis.speed_mps, analysis.speed_status or "estimated", "m/s"),
            "asymmetry_pct": {"value": None, "status": "not_yet_available"},
            "turning": analysis.turning_metrics or {"status": "not_yet_available"},
            "fatigue": analysis.fatigue_metrics or {"status": "not_yet_available"},
            "smoothness": _tagged(analysis.movement_smoothness, "derived", "unitless"),
        },
        "computed_at": analysis.computed_at.isoformat() if analysis.computed_at else None,
    }


@router.get("/{session_id}/quality")
def get_quality(session_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    analysis = db.query(GaitAnalysis).filter(GaitAnalysis.session_id == session_id).first()
    if not analysis:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Quality data not yet available")
    return {
        "quality_score": analysis.quality_score,
        "flags": (analysis.quality_flags or {}).get("flags", []),
    }


@router.get("/{session_id}/raw/{recording_id}")
def get_raw_signal(
    session_id: uuid.UUID,
    recording_id: uuid.UUID,
    max_points: int = 2000,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    recording = db.query(SensorRecording).filter(
        SensorRecording.recording_id == recording_id, SensorRecording.session_id == session_id
    ).first()
    if not recording:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recording not found")

    df = pd.read_csv(recording.raw_file_path)
    if len(df) > max_points:
        step = len(df) // max_points
        df = df.iloc[::step]

    return {
        "recording_id": str(recording_id),
        "n_points": len(df),
        "downsampled": len(df) < (recording.n_samples or len(df)),
        "data": df.to_dict(orient="list"),
    }


@router.post("/{session_id}/notes", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(session_id: uuid.UUID, payload: NoteCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = db.query(GaitSession).get(session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    note = ClinicalNote(session_id=session_id, clinician_id=user.user_id, **payload.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    record_audit(db, user, "create_note", "clinical_notes", note.note_id)
    return note


@router.get("/{session_id}/notes", response_model=List[NoteOut])
def list_notes(session_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(ClinicalNote).filter(ClinicalNote.session_id == session_id).order_by(ClinicalNote.created_at.desc()).all()


@router.post("/{session_id}/report")
def create_report(session_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = db.query(GaitSession).get(session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    if session.status != SessionStatus.complete:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Session analysis is not complete yet")

    report_path = generate_report_pdf(db, session)

    report = Report(
        session_id=session_id,
        report_file_path=report_path,
        report_version="1.0.0",
        generated_by=user.user_id,
    )
    db.add(report)
    db.commit()
    record_audit(db, user, "generate_report", "reports", report.report_id)
    return {"report_id": str(report.report_id), "report_file_path": report_path}


@router.get("/{session_id}/report")
def get_report(session_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = (
        db.query(Report)
        .filter(Report.session_id == session_id)
        .order_by(Report.generated_at.desc())
        .first()
    )
    if not report:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No report generated yet")
    return {"report_id": str(report.report_id), "report_file_path": report.report_file_path, "generated_at": report.generated_at.isoformat()}


@router.get("/{session_id}/report/download")
def download_report(session_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = (
        db.query(Report)
        .filter(Report.session_id == session_id)
        .order_by(Report.generated_at.desc())
        .first()
    )
    if not report:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No report generated yet")
    return FileResponse(report.report_file_path, media_type="application/pdf", filename="neurogait_report.pdf")
