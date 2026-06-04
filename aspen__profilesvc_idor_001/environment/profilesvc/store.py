from __future__ import annotations
from profilesvc.models import Profile, ExperienceEntry
import uuid

_db: dict[str, Profile] = {}


def reset() -> None:
    _db.clear()


def create(
    owner_id: str,
    display_name: str,
    headline: str = "",
    skills: list | None = None,
    experience: list | None = None,
    private_summary: str = "",
    documents: dict | None = None,
    collaborators: list | None = None,
    visibility: str = "private",
) -> Profile:
    p = Profile(
        id=uuid.uuid4().hex[:8],
        owner_id=owner_id,
        display_name=display_name,
        headline=headline,
        skills=skills or [],
        experience=experience or [],
        private_summary=private_summary,
        documents=documents or {},
        collaborators=collaborators or [],
        visibility=visibility,
    )
    _db[p.id] = p
    return p


def get(profile_id: str) -> Profile | None:
    return _db.get(profile_id)


def list_all() -> list[Profile]:
    return list(_db.values())


def update(profile_id: str, **kwargs) -> Profile | None:
    p = _db.get(profile_id)
    if p is None:
        return None
    data = p.model_dump()
    data.update({k: v for k, v in kwargs.items() if v is not None})
    _db[profile_id] = Profile(**data)
    return _db[profile_id]
