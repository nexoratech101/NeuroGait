from pathlib import Path

import numpy as np
import pandas as pd

from app.pipeline.bout_detection import detect_walking_bouts
from app.pipeline.event_detection import detect_gait_events
from app.pipeline.filtering import lowpass_filter
from app.pipeline.gravity_compensation import compensate_gravity
from app.pipeline.motion_signal import vector_magnitude
from app.pipeline.qc import run_qc

FIXTURE = Path(__file__).parent / "fixtures" / "session_20260813_111730.csv"


def _motion_signal_from_fixture():
    df = pd.read_csv(FIXTURE)
    qc = run_qc(df)
    fs = qc.sampling_rate_hz_estimated
    accel = df[["accel_x", "accel_y", "accel_z"]].to_numpy(dtype=float)
    for axis in range(3):
        accel[:, axis] = lowpass_filter(accel[:, axis], fs)
    gravity_result = compensate_gravity(accel, fs)
    return vector_magnitude(gravity_result.dynamic_accel), fs


def test_walking_bouts_detected_on_fixture():
    motion_mag, fs = _motion_signal_from_fixture()
    bouts = detect_walking_bouts(motion_mag, fs)
    assert len(bouts) >= 1
    for bout in bouts:
        assert bout.duration_s >= 5.0


def test_no_bouts_on_flat_signal():
    fs = 50.0
    flat_signal = np.zeros(500)
    bouts = detect_walking_bouts(flat_signal, fs)
    assert bouts == []


def test_gait_events_detected_within_bout():
    motion_mag, fs = _motion_signal_from_fixture()
    bouts = detect_walking_bouts(motion_mag, fs)
    assert bouts, "fixture should contain at least one walking bout"
    events = detect_gait_events(motion_mag, fs, bouts[0])
    assert len(events) > 0
    for e in events:
        assert bouts[0].start_idx <= e.index <= bouts[0].end_idx
