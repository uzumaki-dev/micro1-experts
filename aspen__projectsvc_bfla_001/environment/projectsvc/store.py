from __future__ import annotations
from projectsvc.models import Project, AuditEvent

_db: dict[str, Project] = {}


def reset() -> None:
    _db.clear()


def create(owner_id: str, name: str, description: str = "") -> Project:
    p = Project(
        name=name,
        description=description,
        owner_id=owner_id,
        members={owner_id: "admin"},
        audit_log=[AuditEvent(event_type="created", actor_id=owner_id)],
    )
    _db[p.id] = p
    return p


def get(project_id: str) -> Project | None:
    return _db.get(project_id)


def list_for_user(user_id: str, is_superadmin: bool = False) -> list[Project]:
    if is_superadmin:
        return list(_db.values())
    return [p for p in _db.values() if user_id in p.members]


def delete(project_id: str) -> bool:
    if project_id in _db:
        del _db[project_id]
        return True
    return False


def update(project_id: str, **kwargs) -> Project | None:
    p = _db.get(project_id)
    if p is None:
        return None
    updated = p.model_copy(update=kwargs)
    _db[project_id] = updated
    return updated
