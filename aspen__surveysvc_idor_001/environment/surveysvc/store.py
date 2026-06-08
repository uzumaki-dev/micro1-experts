from __future__ import annotations
from surveysvc.models import Survey

_store: dict[str, Survey] = {}


def reset() -> None:
    _store.clear()


def create(
    owner_id: str,
    title: str = "Untitled Survey",
    description: str = "",
    status: str = "draft",
    visibility: str = "private",
    collaborators: list | None = None,
    internal_notes: str = "",
    responses: list | None = None,
    attachments: dict | None = None,
) -> Survey:
    s = Survey(
        owner_id=owner_id,
        title=title,
        description=description,
        status=status,
        visibility=visibility,
        collaborators=collaborators or [],
        internal_notes=internal_notes,
        responses=responses or [],
        attachments=attachments or {},
    )
    _store[s.id] = s
    return s


def get(survey_id: str) -> Survey | None:
    return _store.get(survey_id)


def list_all() -> list[Survey]:
    return list(_store.values())


def update(survey_id: str, **kwargs) -> Survey | None:
    s = _store.get(survey_id)
    if s is None:
        return None
    data = s.model_dump()
    data.update(kwargs)
    updated = Survey(**data)
    _store[survey_id] = updated
    return updated
