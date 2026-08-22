"""Stage 16: PDF report generation (WeasyPrint), with mandatory footer preserved
verbatim from spec section 10 and measured/estimated/derived tags carried through."""
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session
from weasyprint import HTML

from app.config import REPORT_DIR
from app.models import ClinicalNote, GaitAnalysis, GaitSession, Patient
from app.pipeline.trend import TrendPoint, build_trend_series

TEMPLATE_DIR = Path(__file__).parent / "reports" / "templates"
_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

METRIC_LABELS = [
    ("cadence_spm", "Cadence", "steps/min", "cadence_status"),
    ("step_time_s", "Step time", "s", None),
    ("stride_time_s", "Stride time", "s", None),
    ("gait_regularity_index", "Gait regularity index", "unitless", None),
    ("speed_mps", "Walking speed (research metric)", "m/s", "speed_status"),
]


def generate_report_pdf(db: Session, session: GaitSession) -> str:
    patient = db.query(Patient).get(session.patient_id)
    analysis = db.query(GaitAnalysis).filter(GaitAnalysis.session_id == session.session_id).first()
    notes = (
        db.query(ClinicalNote)
        .filter(ClinicalNote.session_id == session.session_id)
        .order_by(ClinicalNote.created_at.desc())
        .all()
    )

    metrics = []
    for field, label, unit, status_field in METRIC_LABELS:
        value = getattr(analysis, field) if analysis else None
        status = (getattr(analysis, status_field) if status_field and analysis else None) or "derived"
        metrics.append({"label": label, "value": value, "unit": unit, "status": status})

    sibling_rows = (
        db.query(GaitSession, GaitAnalysis)
        .join(GaitAnalysis, GaitAnalysis.session_id == GaitSession.session_id)
        .filter(GaitSession.patient_id == session.patient_id)
        .order_by(GaitSession.assessment_date.asc())
        .all()
    )

    comparisons = []
    for field, label, unit, status_field in METRIC_LABELS:
        points = [
            TrendPoint(
                session_id=str(s.session_id),
                assessment_date=s.assessment_date.isoformat() if s.assessment_date else "",
                value=getattr(a, field),
                status="derived",
            )
            for s, a in sibling_rows
        ]
        series = build_trend_series(field, points)
        comp = series["comparison"]
        comp["metric"] = label
        comparisons.append(comp)

    template = _env.get_template("report.html")
    html_content = template.render(
        generated_at=datetime.now(timezone.utc).isoformat(),
        patient=patient,
        session=session,
        quality_score=(analysis.quality_score if analysis else None),
        quality_flags=((analysis.quality_flags or {}).get("flags", []) if analysis else []),
        metrics=metrics,
        comparisons=comparisons,
        notes=notes,
    )

    report_dir = REPORT_DIR / str(session.session_id)
    report_dir.mkdir(parents=True, exist_ok=True)
    output_path = report_dir / f"report_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.pdf"

    HTML(string=html_content).write_pdf(str(output_path))
    return str(output_path)
