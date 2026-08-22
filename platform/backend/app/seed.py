"""Seeds demo users, a demo patient, and a demo session built from the sample
fixture CSV. Run inside the backend container: `python -m app.seed`."""
import shutil
from pathlib import Path

from app.database import Base, SessionLocal, engine
from app.models import Patient, SensorPosition, SensorRecording, GaitSession, SessionStatus, User, UserRole
from app.pipeline.qc import run_qc
from app.pipeline_service import run_session_processing
from app.security import hash_password
from app.storage import save_raw_file

FIXTURE_PATH = Path(__file__).parent.parent / "tests" / "fixtures" / "session_20260813_111730.csv"


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == "admin@neurogait.example.com").first():
            print("Seed data already present, skipping.")
            return

        admin = User(name="Admin User", email="admin@neurogait.example.com", role=UserRole.admin, password_hash=hash_password("changeme123"))
        physician = User(name="Dr. Demo Physician", email="physician@neurogait.example.com", role=UserRole.physician, password_hash=hash_password("changeme123"))
        db.add_all([admin, physician])
        db.flush()

        patient = Patient(
            study_id="STU-0001",
            full_name="Demo Patient",
            sex="female",
            ms_phenotype="relapsing-remitting",
            mobility_status="ambulatory, no aid",
            treating_physician_id=physician.user_id,
            consent_recorded=True,
        )
        db.add(patient)
        db.flush()

        session = GaitSession(
            patient_id=patient.patient_id,
            test_type="10m walk",
            conditions={"surface": "indoor", "shoes": "regular", "assistive_device": "none"},
            clinician_id=physician.user_id,
            status=SessionStatus.uploaded,
        )
        db.add(session)
        db.flush()

        content = FIXTURE_PATH.read_bytes()
        raw_path, file_hash = save_raw_file(str(session.session_id), FIXTURE_PATH.name, content)

        import pandas as pd
        df = pd.read_csv(raw_path)
        qc = run_qc(df)

        recording = SensorRecording(
            session_id=session.session_id,
            position_claimed=SensorPosition.hip,
            raw_file_path=raw_path,
            raw_file_hash=file_hash,
            sampling_rate_hz_estimated=qc.sampling_rate_hz_estimated,
            n_samples=qc.n_samples,
            duration_s=qc.duration_s,
            gap_count=qc.gap_count,
        )
        db.add(recording)
        db.commit()

        run_session_processing(str(session.session_id))
        print(f"Seeded demo patient {patient.study_id} with session {session.session_id}")
        print("Login: admin@neurogait.example.com / changeme123 or physician@neurogait.example.com / changeme123")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
