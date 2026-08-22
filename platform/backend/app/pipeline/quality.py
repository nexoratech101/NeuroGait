"""Stage 13: combine QC/pipeline signals into a Data Quality Score with plain-language reasons."""
from dataclasses import dataclass, field
from typing import List

from app.pipeline.qc import QCResult


@dataclass
class QualityResult:
    quality_score: float  # 0-100
    flags: List[str] = field(default_factory=list)


def compute_quality_score(qc: QCResult, n_walking_bouts: int, position_plausible: bool) -> QualityResult:
    score = 100.0
    flags: List[str] = []

    if qc.n_samples < 10:
        score -= 40
        flags.append("Very few samples recorded")

    gap_penalty = min(qc.gap_count * 3, 25)
    if gap_penalty:
        score -= gap_penalty
        flags.append(f"{qc.gap_count} timing gap(s) in recording (data may be incomplete)")

    if qc.duplicate_timestamp_count:
        score -= min(qc.duplicate_timestamp_count * 2, 10)
        flags.append("Duplicate/out-of-order timestamps present")

    total_saturation = sum(qc.saturation_flags.values())
    if total_saturation:
        score -= min(total_saturation, 15)
        flags.append("Possible sensor saturation detected on one or more axes")

    total_out_of_range = sum(qc.range_flags.values())
    if total_out_of_range:
        score -= min(total_out_of_range, 15)
        flags.append("Samples outside plausible sensor range detected")

    if n_walking_bouts == 0:
        score -= 30
        flags.append("No walking bouts of sufficient duration detected")

    if not position_plausible:
        score -= 10
        flags.append("Claimed sensor position may not match observed signal characteristics")

    if qc.duration_s < 30:
        score -= 10
        flags.append("Recording duration is short for stable gait metrics")

    score = max(0.0, min(100.0, score))
    return QualityResult(quality_score=round(score, 1), flags=flags)
