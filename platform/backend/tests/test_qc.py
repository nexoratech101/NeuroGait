from pathlib import Path

import pandas as pd

from app.pipeline.qc import run_qc

FIXTURE = Path(__file__).parent / "fixtures" / "session_20260813_111730.csv"


def test_qc_on_fixture_detects_expected_rate_and_gaps():
    df = pd.read_csv(FIXTURE)
    result = run_qc(df)
    assert 45 <= result.sampling_rate_hz_estimated <= 55
    assert result.gap_count >= 1  # fixture has injected gaps
    assert result.n_samples == len(df)
    assert result.duration_s > 200


def test_qc_flags_duplicate_timestamps():
    df = pd.DataFrame({
        "timestamp_ms": [0, 20, 20, 60, 80],
        "accel_x": [0.0] * 5, "accel_y": [0.0] * 5, "accel_z": [1.0] * 5,
        "gyro_x": [0.0] * 5, "gyro_y": [0.0] * 5, "gyro_z": [0.0] * 5,
    })
    result = run_qc(df)
    assert result.duplicate_timestamp_count >= 1


def test_qc_flags_saturation():
    n = 100
    df = pd.DataFrame({
        "timestamp_ms": list(range(0, n * 20, 20)),
        "accel_x": [16.0] * n, "accel_y": [0.0] * n, "accel_z": [1.0] * n,
        "gyro_x": [0.0] * n, "gyro_y": [0.0] * n, "gyro_z": [0.0] * n,
    })
    result = run_qc(df)
    assert result.saturation_flags["accel_x"] == n
    assert any("saturation" in w.lower() for w in result.warnings)


def test_qc_no_false_positive_gaps_on_regular_grid():
    n = 500
    df = pd.DataFrame({
        "timestamp_ms": list(range(0, n * 20, 20)),
        "accel_x": [0.0] * n, "accel_y": [0.0] * n, "accel_z": [1.0] * n,
        "gyro_x": [0.0] * n, "gyro_y": [0.0] * n, "gyro_z": [0.0] * n,
    })
    result = run_qc(df)
    assert result.gap_count == 0
