"""Orchestrates pipeline stages 4-14 for a single sensor recording.

Phase 1 computes core gait metrics from one sensor (hip preferred, but works
with any single sensor present -- spec section 12 step 12 / section 7).
When multiple recordings exist in a session, the caller picks the preferred
one via `select_preferred_recording`.
"""
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd

from app.pipeline.bout_detection import detect_walking_bouts
from app.pipeline.clinical_metrics import ClinicalMetricsPackage, package_clinical_metrics
from app.pipeline.event_detection import detect_gait_events
from app.pipeline.features import extract_features
from app.pipeline.filtering import lowpass_filter
from app.pipeline.gravity_compensation import compensate_gravity
from app.pipeline.motion_signal import vector_magnitude
from app.pipeline.position_plausibility import check_position_plausibility
from app.pipeline.qc import QCResult, run_qc
from app.pipeline.quality import compute_quality_score
from app.pipeline.segmentation import segment_steps_strides

POSITION_PREFERENCE = ["hip", "thigh_l", "thigh_r", "ankle_l", "ankle_r", "unknown"]


@dataclass
class RecordingPipelineResult:
    qc: QCResult
    n_bouts: int
    n_events: int
    walking_duration_s: float
    metrics: ClinicalMetricsPackage
    position_plausible: bool
    position_confidence: float


def select_preferred_recording(recordings: List[dict]) -> dict:
    """recordings: list of {'position': str, ...}. Returns the preferred one."""
    def rank(rec):
        pos = rec.get("position") or "unknown"
        try:
            return POSITION_PREFERENCE.index(pos)
        except ValueError:
            return len(POSITION_PREFERENCE)

    return sorted(recordings, key=rank)[0]


def run_recording_pipeline(df: pd.DataFrame, claimed_position: str = "unknown") -> RecordingPipelineResult:
    qc = run_qc(df)

    plausibility = check_position_plausibility(df, claimed_position)

    fs_hz = qc.sampling_rate_hz_estimated
    accel = df[["accel_x", "accel_y", "accel_z"]].to_numpy(dtype=float)

    if fs_hz > 0 and len(accel) > 10:
        for axis in range(3):
            accel[:, axis] = lowpass_filter(accel[:, axis], fs_hz)
        gravity_result = compensate_gravity(accel, fs_hz)
        motion_mag = vector_magnitude(gravity_result.dynamic_accel)
    else:
        motion_mag = np.zeros(len(accel))

    bouts = detect_walking_bouts(motion_mag, fs_hz)
    walking_duration_s = round(sum(b.duration_s for b in bouts), 2)

    all_events = []
    for bout in bouts:
        all_events.extend(detect_gait_events(motion_mag, fs_hz, bout))

    segmentation = segment_steps_strides(all_events)
    features = extract_features(len(all_events), walking_duration_s, segmentation, motion_mag, fs_hz)

    quality = compute_quality_score(qc, len(bouts), plausibility.plausible)
    metrics = package_clinical_metrics(features, walking_duration_s, len(bouts), quality)

    return RecordingPipelineResult(
        qc=qc,
        n_bouts=len(bouts),
        n_events=len(all_events),
        walking_duration_s=walking_duration_s,
        metrics=metrics,
        position_plausible=plausibility.plausible,
        position_confidence=plausibility.confidence,
    )
