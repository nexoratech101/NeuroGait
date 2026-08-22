"""Stage 4: per-sensor quality control.

Sampling is only approximately regular (confirmed from the sample fixture:
median dt ~20ms, max observed gap ~86ms) -- QC must detect and report gaps,
never assume a clean grid.
"""
from dataclasses import dataclass, field
from typing import List

import numpy as np
import pandas as pd

# A gap is flagged when the inter-sample interval exceeds this multiple of
# the median interval (conservative -- avoids flagging normal jitter).
GAP_MULTIPLIER = 2.5
SATURATION_ACCEL_G = 15.5  # near/at IMU accel full-scale range
SATURATION_GYRO_DPS = 2000.0  # near/at IMU gyro full-scale range
ACCEL_SANITY_RANGE = (-16.0, 16.0)
GYRO_SANITY_RANGE = (-2000.0, 2000.0)


@dataclass
class QCResult:
    sampling_rate_hz_estimated: float
    median_dt_ms: float
    n_samples: int
    duration_s: float
    gap_count: int
    gap_locations_ms: List[float] = field(default_factory=list)
    duplicate_timestamp_count: int = 0
    saturation_flags: dict = field(default_factory=dict)
    range_flags: dict = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


def run_qc(df: pd.DataFrame) -> QCResult:
    ts = df["timestamp_ms"].to_numpy(dtype=float)
    dt = np.diff(ts)
    median_dt = float(np.median(dt)) if len(dt) else 0.0
    sampling_rate = 1000.0 / median_dt if median_dt > 0 else 0.0

    gap_threshold = median_dt * GAP_MULTIPLIER if median_dt > 0 else float("inf")
    gap_mask = dt > gap_threshold
    gap_locations = ts[1:][gap_mask].tolist()

    duplicate_count = int((dt <= 0).sum())

    warnings = []
    if len(gap_locations) > 0:
        warnings.append(f"{len(gap_locations)} timing gap(s) detected in the recording")
    if duplicate_count > 0:
        warnings.append(f"{duplicate_count} duplicate/out-of-order timestamp(s) detected")

    saturation_flags = {}
    for axis in ("accel_x", "accel_y", "accel_z"):
        n_sat = int((df[axis].abs() >= SATURATION_ACCEL_G).sum())
        saturation_flags[axis] = n_sat
        if n_sat > 0:
            warnings.append(f"Possible sensor saturation on {axis} ({n_sat} sample(s))")
    for axis in ("gyro_x", "gyro_y", "gyro_z"):
        n_sat = int((df[axis].abs() >= SATURATION_GYRO_DPS).sum())
        saturation_flags[axis] = n_sat
        if n_sat > 0:
            warnings.append(f"Possible sensor saturation on {axis} ({n_sat} sample(s))")

    range_flags = {}
    for axis in ("accel_x", "accel_y", "accel_z"):
        lo, hi = ACCEL_SANITY_RANGE
        n_out = int(((df[axis] < lo) | (df[axis] > hi)).sum())
        range_flags[axis] = n_out
        if n_out > 0:
            warnings.append(f"{n_out} sample(s) on {axis} outside plausible accel range")
    for axis in ("gyro_x", "gyro_y", "gyro_z"):
        lo, hi = GYRO_SANITY_RANGE
        n_out = int(((df[axis] < lo) | (df[axis] > hi)).sum())
        range_flags[axis] = n_out
        if n_out > 0:
            warnings.append(f"{n_out} sample(s) on {axis} outside plausible gyro range")

    duration_s = float((ts[-1] - ts[0]) / 1000.0) if len(ts) > 1 else 0.0

    return QCResult(
        sampling_rate_hz_estimated=round(sampling_rate, 2),
        median_dt_ms=round(median_dt, 2),
        n_samples=len(df),
        duration_s=round(duration_s, 2),
        gap_count=len(gap_locations),
        gap_locations_ms=gap_locations,
        duplicate_timestamp_count=duplicate_count,
        saturation_flags=saturation_flags,
        range_flags=range_flags,
        warnings=warnings,
    )
