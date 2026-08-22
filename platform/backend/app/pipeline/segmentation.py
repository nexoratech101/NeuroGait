"""Stage 11: pair consecutive gait events into steps and strides."""
from dataclasses import dataclass
from typing import List

from app.pipeline.event_detection import GaitEvent


@dataclass
class SegmentationResult:
    step_times_s: List[float]
    stride_times_s: List[float]


def segment_steps_strides(events: List[GaitEvent]) -> SegmentationResult:
    times = sorted(e.time_s for e in events)

    step_times = [round(t2 - t1, 4) for t1, t2 in zip(times, times[1:])]
    # A stride is two consecutive steps (i.e. every other event -> full gait cycle).
    stride_times = [round(t2 - t1, 4) for t1, t2 in zip(times, times[2:])]

    return SegmentationResult(step_times_s=step_times, stride_times_s=stride_times)
