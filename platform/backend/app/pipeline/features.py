"""Stage 12: feature extraction -- the Phase 1 metric floor, computable from one sensor.

Cadence, step/stride time + CV, and an autocorrelation-based regularity index.
"""
from dataclasses import dataclass
from typing import List, Optional

import numpy as np

from app.pipeline.event_detection import GaitEvent
from app.pipeline.segmentation import SegmentationResult


@dataclass
class GaitFeatures:
    cadence_spm: Optional[float]
    step_time_s: Optional[float]
    step_time_cv_pct: Optional[float]
    stride_time_s: Optional[float]
    stride_time_cv_pct: Optional[float]
    gait_regularity_index: Optional[float]


def _mean_cv(values: List[float]):
    if not values:
        return None, None
    arr = np.array(values)
    mean = float(np.mean(arr))
    cv = float(np.std(arr) / mean * 100.0) if mean > 0 else None
    return round(mean, 4), (round(cv, 2) if cv is not None else None)


def compute_cadence(n_events: int, walking_duration_s: float) -> Optional[float]:
    if walking_duration_s <= 0:
        return None
    # cadence in steps per minute; each detected event ~= one step (foot strike/peak)
    return round(n_events / walking_duration_s * 60.0, 1)


def compute_regularity_index(motion_mag: np.ndarray, fs_hz: float) -> Optional[float]:
    """Autocorrelation-based regularity: strength of the dominant gait-cycle periodicity."""
    if fs_hz <= 0 or len(motion_mag) < int(fs_hz * 2):
        return None

    signal = motion_mag - np.mean(motion_mag)
    autocorr = np.correlate(signal, signal, mode="full")
    autocorr = autocorr[len(autocorr) // 2:]
    if autocorr[0] == 0:
        return None
    autocorr = autocorr / autocorr[0]

    # Search for the first strong peak after the zero-lag, within a plausible
    # gait-cycle-time window (0.3s - 2.5s per cycle).
    min_lag = int(0.3 * fs_hz)
    max_lag = min(int(2.5 * fs_hz), len(autocorr) - 1)
    if min_lag >= max_lag:
        return None

    window = autocorr[min_lag:max_lag]
    if len(window) == 0:
        return None

    peak_value = float(np.max(window))
    return round(max(min(peak_value, 1.0), 0.0), 3)


def extract_features(
    n_events: int,
    walking_duration_s: float,
    segmentation: SegmentationResult,
    motion_mag: np.ndarray,
    fs_hz: float,
) -> GaitFeatures:
    cadence = compute_cadence(n_events, walking_duration_s)
    step_time, step_cv = _mean_cv(segmentation.step_times_s)
    stride_time, stride_cv = _mean_cv(segmentation.stride_times_s)
    regularity = compute_regularity_index(motion_mag, fs_hz)

    return GaitFeatures(
        cadence_spm=cadence,
        step_time_s=step_time,
        step_time_cv_pct=step_cv,
        stride_time_s=stride_time,
        stride_time_cv_pct=stride_cv,
        gait_regularity_index=regularity,
    )
