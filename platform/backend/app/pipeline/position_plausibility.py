"""Stage 5: sanity-check the claimed sensor position against signal characteristics.

This is a heuristic WARNING only, never a hard rejection -- refine with more
sensor-position data over time (Future work).
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

# Rough heuristic: distal sensors (ankle) show much higher acceleration
# variance during walking than proximal sensors (hip).
ANKLE_VARIANCE_FLOOR_G2 = 0.15


@dataclass
class PositionPlausibilityResult:
    plausible: bool
    confidence: float
    reason: str


def check_position_plausibility(df: pd.DataFrame, claimed_position: str) -> PositionPlausibilityResult:
    accel_mag = np.sqrt(df["accel_x"] ** 2 + df["accel_y"] ** 2 + df["accel_z"] ** 2)
    variance = float(accel_mag.var())

    if claimed_position in ("ankle_l", "ankle_r"):
        if variance < ANKLE_VARIANCE_FLOOR_G2:
            return PositionPlausibilityResult(
                plausible=False,
                confidence=0.4,
                reason="Signal variance is lower than typically expected at the ankle",
            )
        return PositionPlausibilityResult(plausible=True, confidence=0.7, reason="Variance consistent with ankle placement")

    if claimed_position == "hip":
        if variance > ANKLE_VARIANCE_FLOOR_G2 * 3:
            return PositionPlausibilityResult(
                plausible=False,
                confidence=0.4,
                reason="Signal variance is higher than typically expected at the hip",
            )
        return PositionPlausibilityResult(plausible=True, confidence=0.6, reason="Variance consistent with hip placement")

    return PositionPlausibilityResult(plausible=True, confidence=0.3, reason="No strong heuristic available for this position")
