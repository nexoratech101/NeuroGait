"""Stage 7: estimate gravity from a detected still period and remove it.

Units are assumed g / deg/s per the sample fixture (accel range ~+-2,
gyro range up to ~360) -- NOT yet verified against firmware, see
Open Decision #3 in the spec. This module trusts that assumption.
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class GravityCompensationResult:
    dynamic_accel: np.ndarray  # shape (n, 3), gravity removed
    gravity_vector: np.ndarray  # shape (3,)
    still_period_found: bool


def _find_still_window(accel: np.ndarray, fs_hz: float, window_s: float = 1.0):
    """Find the lowest-variance window of `window_s` seconds; treat it as 'still'."""
    win = max(int(window_s * fs_hz), 5)
    if len(accel) < win:
        return 0, len(accel)

    mag = np.linalg.norm(accel, axis=1)
    best_start, best_var = 0, np.inf
    step = max(win // 4, 1)
    for start in range(0, len(mag) - win, step):
        seg_var = float(np.var(mag[start:start + win]))
        if seg_var < best_var:
            best_var = seg_var
            best_start = start
    return best_start, best_start + win


def compensate_gravity(accel: np.ndarray, fs_hz: float) -> GravityCompensationResult:
    start, end = _find_still_window(accel, fs_hz)
    still_segment = accel[start:end]
    gravity_vector = np.mean(still_segment, axis=0) if len(still_segment) > 0 else np.array([0.0, 0.0, 1.0])

    # Still-period variance threshold: real "still" samples in g-units cluster
    # tightly; a high-variance "best" window means no genuine still period existed.
    still_found = float(np.var(np.linalg.norm(still_segment, axis=1))) < 0.01 if len(still_segment) else False

    dynamic_accel = accel - gravity_vector
    return GravityCompensationResult(dynamic_accel=dynamic_accel, gravity_vector=gravity_vector, still_period_found=still_found)
