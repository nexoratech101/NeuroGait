import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import GaitAnalysis, GaitSession, Patient, User
from app.pipeline.trend import TrendPoint, build_trend_series

router = APIRouter(prefix="/patients", tags=["trend"])

METRICS = [
    ("cadence_spm", "cadence_status"),
    ("step_time_s", None),
    ("stride_time_s", None),
    ("gait_regularity_index", None),
    ("speed_mps", "speed_status"),
]


@router.get("/{patient_id}/trend")
def get_patient_trend(patient_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    patient = db.query(Patient).get(patient_id)
    if not patient:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found")

    rows = (
        db.query(GaitSession, GaitAnalysis)
        .join(GaitAnalysis, GaitAnalysis.session_id == GaitSession.session_id)
        .filter(GaitSession.patient_id == patient_id)
        .order_by(GaitSession.assessment_date.asc())
        .all()
    )

    trends = {}
    for metric_field, status_field in METRICS:
        points = [
            TrendPoint(
                session_id=str(session.session_id),
                assessment_date=session.assessment_date.isoformat() if session.assessment_date else "",
                value=getattr(analysis, metric_field),
                status=(getattr(analysis, status_field) if status_field else "derived") or "derived",
            )
            for session, analysis in rows
        ]
        trends[metric_field] = build_trend_series(metric_field, points)

    return {"patient_id": str(patient_id), "n_sessions": len(rows), "trends": trends}
