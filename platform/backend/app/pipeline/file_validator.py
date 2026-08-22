"""Stage 1: validate an uploaded sensor CSV before anything else touches it."""
from dataclasses import dataclass, field

import pandas as pd

REQUIRED_COLUMNS = [
    "timestamp_ms",
    "accel_x",
    "accel_y",
    "accel_z",
    "gyro_x",
    "gyro_y",
    "gyro_z",
]


@dataclass
class ValidationResult:
    valid: bool
    errors: list = field(default_factory=list)
    n_rows: int = 0


def validate_file(path: str) -> ValidationResult:
    errors = []
    try:
        df = pd.read_csv(path)
    except Exception as exc:  # malformed / unparseable CSV
        return ValidationResult(valid=False, errors=[f"Could not parse CSV: {exc}"], n_rows=0)

    if df.empty:
        return ValidationResult(valid=False, errors=["File contains no rows"], n_rows=0)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")

    if not missing:
        non_numeric = [c for c in REQUIRED_COLUMNS if not pd.api.types.is_numeric_dtype(df[c])]
        if non_numeric:
            errors.append(f"Non-numeric data in columns: {', '.join(non_numeric)}")

    return ValidationResult(valid=len(errors) == 0, errors=errors, n_rows=len(df))
