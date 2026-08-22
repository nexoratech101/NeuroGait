"""Stage 15: compare current session to previous and baseline sessions.

Absolute + percentage change only, neutral descriptive language --
never diagnostic/prognostic wording (spec section 0.1).
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TrendPoint:
    session_id: str
    assessment_date: str
    value: Optional[float]
    status: str


@dataclass
class TrendComparison:
    metric: str
    current: Optional[float]
    previous: Optional[float]
    baseline: Optional[float]
    change_vs_previous_abs: Optional[float]
    change_vs_previous_pct: Optional[float]
    change_vs_baseline_abs: Optional[float]
    change_vs_baseline_pct: Optional[float]


def _pct_change(old: Optional[float], new: Optional[float]) -> Optional[float]:
    if old is None or new is None or old == 0:
        return None
    return round((new - old) / abs(old) * 100.0, 1)


def compare_metric(metric_name: str, current: Optional[float], previous: Optional[float], baseline: Optional[float]) -> TrendComparison:
    return TrendComparison(
        metric=metric_name,
        current=current,
        previous=previous,
        baseline=baseline,
        change_vs_previous_abs=(round(current - previous, 3) if current is not None and previous is not None else None),
        change_vs_previous_pct=_pct_change(previous, current),
        change_vs_baseline_abs=(round(current - baseline, 3) if current is not None and baseline is not None else None),
        change_vs_baseline_pct=_pct_change(baseline, current),
    )


def build_trend_series(metric_name: str, points: List[TrendPoint]) -> dict:
    """Build a plain time series for charting, plus current-vs-previous/baseline comparison."""
    ordered = sorted(points, key=lambda p: p.assessment_date)
    current = ordered[-1] if ordered else None
    previous = ordered[-2] if len(ordered) >= 2 else None
    baseline = ordered[0] if ordered else None

    comparison = compare_metric(
        metric_name,
        current.value if current else None,
        previous.value if previous else None,
        baseline.value if baseline and baseline is not current else None,
    )

    return {
        "metric": metric_name,
        "series": [
            {"session_id": p.session_id, "assessment_date": p.assessment_date, "value": p.value, "status": p.status}
            for p in ordered
        ],
        "comparison": comparison.__dict__,
    }
