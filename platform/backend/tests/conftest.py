import os
import tempfile
from pathlib import Path

import pytest

_tmp_dir = tempfile.mkdtemp(prefix="neurogait_test_")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_tmp_dir}/test.db")
os.environ.setdefault("RAW_DATA_DIR", f"{_tmp_dir}/raw")
os.environ.setdefault("PROCESSED_DATA_DIR", f"{_tmp_dir}/processed")
os.environ.setdefault("REPORT_DIR", f"{_tmp_dir}/reports")

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User, UserRole  # noqa: E402
from app.security import hash_password  # noqa: E402

FIXTURE_CSV = Path(__file__).parent / "fixtures" / "session_20260813_111730.csv"


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def test_user(db_session):
    email = "tester@neurogait.example.com"
    user = db_session.query(User).filter(User.email == email).first()
    if not user:
        user = User(name="Tester", email=email, role=UserRole.admin, password_hash=hash_password("testpass123"))
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture()
def auth_headers(client, test_user):
    resp = client.post("/auth/login", json={"email": test_user.email, "password": "testpass123"})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
