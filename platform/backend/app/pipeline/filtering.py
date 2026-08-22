"""Stage 6: filtering. Butterworth low-pass (~20 Hz) plus optional high-pass (~0.5 Hz) for drift."""
import numpy as np
from scipy.signal import butter, filtfilt


def _butter_filter(data: np.ndarray, cutoff_hz: float, fs_hz: float, btype: str, order: int = 4) -> np.ndarray:
    nyq = fs_hz / 2.0
    normal_cutoff = min(cutoff_hz / nyq, 0.99)
    b, a = butter(order, normal_cutoff, btype=btype)
    # padlen must be shorter than the signal or filtfilt raises.
    padlen = min(3 * max(len(a), len(b)), len(data) - 1)
    if padlen < 0:
        return data
    return filtfilt(b, a, data, padlen=padlen)


def lowpass_filter(data: np.ndarray, fs_hz: float, cutoff_hz: float = 20.0) -> np.ndarray:
    if len(data) < 10 or fs_hz <= 0:
        return data
    return _butter_filter(data, cutoff_hz, fs_hz, "low")


def highpass_filter(data: np.ndarray, fs_hz: float, cutoff_hz: float = 0.5) -> np.ndarray:
    if len(data) < 10 or fs_hz <= 0:
        return data
    return _butter_filter(data, cutoff_hz, fs_hz, "high")
