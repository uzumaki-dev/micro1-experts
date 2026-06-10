from __future__ import annotations
import uuid
from candidatesvc.models import Assessment, Candidate

_candidates: dict[str, Candidate] = {}


def reset() -> None:
    _candidates.clear()


def create(
    owner_id: str,
    name: str,
    position: str = "",
    status: str = "pending",
    screening_notes: str = "",
    assessments: list[Assessment] | None = None,
    documents: dict[str, str] | None = None,
    interviewer_ids: list[str] | None = None,
    visibility: str = "private",
) -> Candidate:
    c = Candidate(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        name=name,
        position=position,
        status=status,
        screening_notes=screening_notes,
        assessments=assessments or [],
        documents=documents or {},
        interviewer_ids=interviewer_ids or [],
        visibility=visibility,
    )
    _candidates[c.id] = c
    return c


def get(candidate_id: str) -> Candidate | None:
    return _candidates.get(candidate_id)


def list_all() -> list[Candidate]:
    return list(_candidates.values())


def update(candidate_id: str, **kwargs) -> Candidate | None:
    c = _candidates.get(candidate_id)
    if c is None:
        return None
    updated = c.model_copy(update={k: v for k, v in kwargs.items()})
    _candidates[candidate_id] = updated
    return updated
