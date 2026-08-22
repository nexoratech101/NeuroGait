"""Stage 3: match extracted filename metadata to an existing patient, or signal
that manual selection/creation is needed. Pure matching logic; the router layer
does the actual DB lookup and passes in candidate study IDs."""
from dataclasses import dataclass
from typing import List, Optional

from app.pipeline.metadata_extractor import FileMetadata


@dataclass
class AssociationResult:
    matched_study_id: Optional[str]
    needs_manual_association: bool
    reason: str


def resolve_association(metadata: FileMetadata, known_study_ids: List[str]) -> AssociationResult:
    if not metadata.has_metadata or not metadata.patient_study_id:
        return AssociationResult(None, True, "No patient metadata found in filename")

    candidates = [sid for sid in known_study_ids if sid.lower() == metadata.patient_study_id.lower()]
    if len(candidates) == 1:
        return AssociationResult(candidates[0], False, "Matched existing patient by filename metadata")

    return AssociationResult(None, True, "Filename references an unknown patient study ID")
