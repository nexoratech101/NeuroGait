"""Stage 14: package pipeline outputs, tagging each metric measured/estimated/derived.

Rule (spec section 0.2): every derived gait metric carries a measured/estimated/derived
tag in every API response and UI display. Never show an estimated value without the tag.
"""
from dataclasses import dataclass, field
from typing import Optional

from app.config import PROCESSING_VERSION
from app.pipeline.features import GaitFeatures
from app.pipeline.quality import QualityResult


@dataclass
class MetricValue:
    value: Optional[float]
    status: str  # 'measured' | 'estimated' | 'derived'
    unit: str


@dataclass
class ClinicalMetricsPackage:
    algorithm_version: str
    walking_duration_s: Optional[float]
    n_walking_bouts: int
    cadence: MetricValue
    step_time: MetricValue
    step_time_cv: MetricValue
    stride_time: MetricValue
    stride_time_cv: MetricValue
    gait_regularity_index: MetricValue
    # Estimated, research-only, disabled by default in the core dashboard (Section 6/7).
    speed: MetricValue
    stride_length: MetricValue
    # Future placeholders -- always null/not-yet-available in Phase 1.
    asymmetry: MetricValue = field(default_factory=lambda: MetricValue(None, "derived", "%"))
    turning: dict = field(default_factory=lambda: {"status": "not_yet_available"})
    fatigue: dict = field(default_factory=lambda: {"status": "not_yet_available"})
    smoothness: MetricValue = field(default_factory=lambda: MetricValue(None, "derived", "unitless"))
    quality: QualityResult = None


def package_clinical_metrics(features: GaitFeatures, walking_duration_s: float, n_bouts: int, quality: QualityResult) -> ClinicalMetricsPackage:
    return ClinicalMetricsPackage(
        algorithm_version=PROCESSING_VERSION,
        walking_duration_s=walking_duration_s,
        n_walking_bouts=n_bouts,
        cadence=MetricValue(features.cadence_spm, "measured", "steps/min"),
        step_time=MetricValue(features.step_time_s, "measured", "s"),
        step_time_cv=MetricValue(features.step_time_cv_pct, "measured", "%"),
        stride_time=MetricValue(features.stride_time_s, "measured", "s"),
        stride_time_cv=MetricValue(features.stride_time_cv_pct, "measured", "%"),
        gait_regularity_index=MetricValue(features.gait_regularity_index, "derived", "unitless"),
        # Speed/stride-length regression model not yet implemented (Future work,
        # spec section 6) -- always null, always tagged 'estimated', never in core summary.
        speed=MetricValue(None, "estimated", "m/s"),
        stride_length=MetricValue(None, "estimated", "m"),
        quality=quality,
    )
