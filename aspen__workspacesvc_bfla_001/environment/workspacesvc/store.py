from __future__ import annotations
from workspacesvc.models import Workspace, WorkspaceSettings, AuditEvent

_db: dict[str, Workspace] = {}


def reset() -> None:
    _db.clear()


def create(owner_id: str, name: str) -> Workspace:
    w = Workspace(
        name=name,
        owner_id=owner_id,
        members={owner_id: "owner"},
        settings=WorkspaceSettings(billing_email=f"{owner_id}@example.com"),
        audit_log=[AuditEvent(event_type="created", actor_id=owner_id)],
    )
    _db[w.id] = w
    return w


def get(ws_id: str) -> Workspace | None:
    return _db.get(ws_id)


def delete(ws_id: str) -> bool:
    if ws_id in _db:
        del _db[ws_id]
        return True
    return False


def update(ws_id: str, **kwargs) -> Workspace | None:
    w = _db.get(ws_id)
    if w is None:
        return None
    updated = w.model_copy(update=kwargs)
    _db[ws_id] = updated
    return updated
