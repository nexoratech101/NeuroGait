"""Stage 9: walking bout detection via windowed energy/variance threshold."""
from dataclasses import dataclass
from typing import List

import numpy as np

MIN_BOUT_DURATION_S = 5.0
WINDOW_S = 1.0


def _otsu_threshold(values: np.ndarray, n_bins: int = 64) -> float:
    """Binary threshold that maximizes between-class variance (Otsu's method).

    Used to separate low-energy (still/pause) windows from high-energy
    (walking) windows without assuming a fixed proportion of either.
    """
    hist, bin_edges = np.histogram(values, bins=n_bins)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0
    weight = hist.astype(float)
    total = weight.sum()
    if total == 0:
        return float(np.median(values)) if len(values) else 0.0

    w1 = np.cumsum(weight)
    w2 = total - w1
    sum_all = np.sum(weight * bin_centers)
    sum1 = np.cumsum(weight * bin_centers)

    with np.errstate(divide="ignore", invalid="ignore"):
        mean1 = np.where(w1 > 0, sum1 / w1, 0)
        mean2 = np.where(w2 > 0, (sum_all - sum1) / w2, 0)
        between_var = w1 * w2 * (mean1 - mean2) ** 2

    idx = int(np.argmax(between_var))
    return float(bin_centers[idx])


@dataclass
class WalkingBout:
    start_idx: int
    end_idx: int
    start_s: float
    end_s: float
    duration_s: float


def detect_walking_bouts(motion_mag: np.ndarray, fs_hz: float, energy_threshold: float = None) -> List[WalkingBout]:
    if fs_hz <= 0 or len(motion_mag) == 0:
        return []

    win = max(int(WINDOW_S * fs_hz), 1)
    n_windows = len(motion_mag) // win
    if n_windows == 0:
        return []

    window_energy = np.array([
        np.var(motion_mag[i * win:(i + 1) * win]) for i in range(n_windows)
    ])

    if energy_threshold is None:
        if np.ptp(window_energy) == 0:
            energy_threshold = float(window_energy[0]) + 1e-6
        else:
            energy_threshold = _otsu_threshold(window_energy)

    active_mask = window_energy > energy_threshold

    bouts = []
    i = 0
    while i < len(active_mask):
        if active_mask[i]:
            j = i
            while j < len(active_mask) and active_mask[j]:
                j += 1
            start_idx = i * win
            end_idx = min(j * win, len(motion_mag))
            duration_s = (end_idx - start_idx) / fs_hz
            if duration_s >= MIN_BOUT_DURATION_S:
                bouts.append(WalkingBout(
                    start_idx=start_idx,
                    end_idx=end_idx,
                    start_s=start_idx / fs_hz,
                    end_s=end_idx / fs_hz,
                    duration_s=duration_s,
                ))
            i = j
        else:
            i += 1

    return bouts
