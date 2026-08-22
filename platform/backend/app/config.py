"""Application configuration, read from environment variables."""
import os
from pathlib import Path

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg2://neurogait:neurogait@db:5432/neurogait"
)

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "480"))

RAW_DATA_DIR = Path(os.environ.get("RAW_DATA_DIR", "/data/raw"))
PROCESSED_DATA_DIR = Path(os.environ.get("PROCESSED_DATA_DIR", "/data/processed"))
REPORT_DIR = Path(os.environ.get("REPORT_DIR", "/data/processed/reports"))

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Bumped whenever the signal-processing pipeline's math/logic changes.
# Every gait_analysis row records the version that produced it so results
# stay reproducible from the raw file at any later date (see spec section 0.4).
PROCESSING_VERSION = "1.0.0"

# Assumed sensor units for Phase 1 (accel in g, gyro in deg/s).
# NOT yet verified against firmware output -- see Open Decision #3 in the spec.
SENSOR_UNITS_VERIFIED = False
