"""Bridges the pure pipeline modules to the database: runs analysis for a session
and writes results back. Invoked via FastAPI BackgroundTasks (spec section 3 --
no Celery/Redis in Phase 1)."""
import pandas as pd

from app.config import PROCESSING_VERSION
from app.database import SessionLocal
from app.models import GaitAnalysis, GaitSession, SensorRecording, SessionStatus
from app.pipeline.pipeline_runner import run_recording_pipeline, select_preferred_recording


def run_session_processing(session_id: str):
    db = SessionLocal()
    try:
        session = db.query(GaitSession).get(session_id)
        if session is None:
            return

        session.status = SessionStatus.processing
        db.commit()

        recordings = db.query(SensorRecording).filter(SensorRecording.session_id == session_id).all()
        if not recordings:
            session.status = SessionStatus.failed
            db.commit()
            return

        candidates = [
            {"position": (r.position_claimed.value if r.position_claimed else "unknown"), "recording": r}
            for r in recordings
        ]
        preferred = select_preferred_recording(candidates)["recording"]

        df = pd.read_csv(preferred.raw_file_path)
        claimed = preferred.position_claimed.value if preferred.position_claimed else "unknown"
        result = run_recording_pipeline(df, claimed_position=claimed)

        preferred.sampling_rate_hz_estimated = result.qc.sampling_rate_hz_estimated
        preferred.n_samples = result.qc.n_samples
        preferred.duration_s = result.qc.duration_s
        preferred.gap_count = result.qc.gap_count
        preferred.position_verified = result.position_plausible
        preferred.position_confidence = result.position_confidence

        metrics = result.metrics
        analysis = GaitAnalysis(
            session_id=session.session_id,
            algorithm_version=PROCESSING_VERSION,
            walking_duration_s=metrics.walking_duration_s,
            n_walking_bouts=metrics.n_walking_bouts,
            cadence_spm=metrics.cadence.value,
            cadence_status=metrics.cadence.status,
            step_time_s=metrics.step_time.value,
            step_time_cv_pct=metrics.step_time_cv.value,
            stride_time_s=metrics.stride_time.value,
            stride_time_cv_pct=metrics.stride_time_cv.value,
            gait_regularity_index=metrics.gait_regularity_index.value,
            speed_mps=metrics.speed.value,
            speed_status=metrics.speed.status,
            gait_asymmetry_pct=None,
            turning_metrics=metrics.turning,
            fatigue_metrics=metrics.fatigue,
            movement_smoothness=metrics.smoothness.value,
            quality_score=metrics.quality.quality_score,
            quality_flags={"flags": metrics.quality.flags},
        )
        db.add(analysis)

        session.status = SessionStatus.complete
        session.processing_version = PROCESSING_VERSION
        db.commit()
    except Exception:
        db.rollback()
        session = db.query(GaitSession).get(session_id)
        if session:
            session.status = SessionStatus.failed
            db.commit()
        raise
    finally:
        db.close()
