"""Stage 2: parse the Phase 1 filename convention, or flag it as legacy/no-metadata.

Convention: PAT-<patient_id>_SES-<date>-<seq>_POS-<ankle|thigh|hip>_DEV-<device_id>.csv
Any file that doesn't match falls through to manual patient association --
this is not an edge case, it's today's actual data (see spec section 4).
"""
import re
from dataclasses import dataclass
from typing import Optional

PATTERN = re.compile(
    r"^PAT-(?P<patient>[\w]+)_SES-(?P<date>\d{8})-(?P<seq>\d+)_"
    r"POS-(?P<position>ankle|thigh|hip)_DEV-(?P<device>[\w]+)",
    re.IGNORECASE,
)


@dataclass
class FileMetadata:
    has_metadata: bool
    patient_study_id: Optional[str] = None
    session_date: Optional[str] = None
    session_seq: Optional[str] = None
    position: Optional[str] = None
    device_serial: Optional[str] = None


def extract_metadata(filename: str) -> FileMetadata:
    match = PATTERN.match(filename)
    if not match:
        return FileMetadata(has_metadata=False)
    d = match.groupdict()
    return FileMetadata(
        has_metadata=True,
        patient_study_id=d["patient"],
        session_date=d["date"],
        session_seq=d["seq"],
        position=d["position"].lower(),
        device_serial=d["device"],
    )
