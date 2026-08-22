"""Stage 10: gait-event detection via peak detection on the motion signal, per bout."""
from dataclasses import dataclass
from typing import List

import numpy as np
from scipy.signal import find_peaks

from app.pipeline.bout_detection import WalkingBout

# Reasonable adult cadence range, used to bound the minimum inter-step interval.
MAX_STEP_RATE_HZ = 3.0  # ~180 steps/min upper bound


@dataclass
class GaitEvent:
    index: int
    time_s: float


def detect_gait_events(motion_mag: np.ndarray, fs_hz: float, bout: WalkingBout) -> List[GaitEvent]:
    if fs_hz <= 0:
        return []

    segment = motion_mag[bout.start_idx:bout.end_idx]
    if len(segment) < 3:
        return []

    min_distance = max(int(fs_hz / MAX_STEP_RATE_HZ), 1)
    prominence = 0.15 * (np.std(segment) or 1.0)

    peaks, _ = find_peaks(segment, distance=min_distance, prominence=prominence)

    events = []
    for p in peaks:
        global_idx = bout.start_idx + p
        events.append(GaitEvent(index=int(global_idx), time_s=float(global_idx / fs_hz)))
    return events
