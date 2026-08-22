from pathlib import Path

import pandas as pd

from app.pipeline.pipeline_runner import run_recording_pipeline

FIXTURE = Path(__file__).parent / "fixtures" / "session_20260813_111730.csv"


def test_cadence_and_stride_time_computed_on_fixture():
    df = pd.read_csv(FIXTURE)
    result = run_recording_pipeline(df, claimed_position="hip")

    cadence = result.metrics.cadence.value
    assert cadence is not None
    # Plausible adult walking cadence range.
    assert 40 <= cadence <= 220
    assert result.metrics.cadence.status == "measured"

    assert result.metrics.step_time.value is not None
    assert result.metrics.step_time.status == "measured"
    assert result.metrics.stride_time.value is not None

    assert result.metrics.gait_regularity_index.status == "derived"
    if result.metrics.gait_regularity_index.value is not None:
        assert 0.0 <= result.metrics.gait_regularity_index.value <= 1.0


def test_speed_is_always_estimated_and_null_in_phase1():
    df = pd.read_csv(FIXTURE)
    result = run_recording_pipeline(df, claimed_position="hip")
    assert result.metrics.speed.status == "estimated"
    assert result.metrics.speed.value is None


def test_future_placeholder_metrics_not_computed():
    df = pd.read_csv(FIXTURE)
    result = run_recording_pipeline(df, claimed_position="hip")
    assert result.metrics.asymmetry.value is None
    assert result.metrics.turning == {"status": "not_yet_available"}
    assert result.metrics.fatigue == {"status": "not_yet_available"}
