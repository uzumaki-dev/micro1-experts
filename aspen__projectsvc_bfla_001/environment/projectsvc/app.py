from __future__ import annotations
from fastapi import FastAPI, Header, HTTPException
from projectsvc import store
from projectsvc.models import (
    Project, ProjectCreate, ProjectPatch,
    MemberAdd, MemberPatch, AuditEvent,
)

app = FastAPI()

SUPERADMIN = "superadmin"


def _require_member(project: Project, user_id: str) -> None:
    if user_id != SUPERADMIN and user_id not in project.members:
        raise HTTPException(status_code=403, detail="Not a project member")


def _require_admin(project: Project, user_id: str) -> None:
    if user_id != SUPERADMIN and project.members.get(user_id) != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")


@app.post("/projects", status_code=201)
def create_project(body: ProjectCreate, x_user_id: str = Header(...)) -> Project:
    return store.create(owner_id=x_user_id, name=body.name, description=body.description)


@app.get("/projects")
def list_projects(x_user_id: str = Header(...)) -> list[Project]:
    return store.list_for_user(x_user_id, is_superadmin=(x_user_id == SUPERADMIN))


@app.get("/projects/{project_id}")
def get_project(project_id: str, x_user_id: str = Header(...)) -> Project:
    p = store.get(project_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    _require_member(p, x_user_id)
    return p


@app.patch("/projects/{project_id}")
def patch_project(
    project_id: str, body: ProjectPatch, x_user_id: str = Header(...)
) -> Project:
    p = store.get(project_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    _require_member(p, x_user_id)
    role = p.members.get(x_user_id, "")
    if x_user_id != SUPERADMIN and role not in ("editor", "admin"):
        raise HTTPException(status_code=403, detail="Editor or admin role required")
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    return store.update(project_id, **updates)  # type: ignore[return-value]


@app.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: str, x_user_id: str = Header(...)) -> None:
    p = store.get(project_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    _require_member(p, x_user_id)
    store.delete(project_id)


@app.post("/projects/{project_id}/archive")
def archive_project(project_id: str, x_user_id: str = Header(...)) -> Project:
    p = store.get(project_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    _require_member(p, x_user_id)
    return store.update(project_id, is_archived=True)  # type: ignore[return-value]


@app.post("/projects/{project_id}/members", status_code=201)
def add_member(
    project_id: str, body: MemberAdd, x_user_id: str = Header(...)
) -> Project:
    p = store.get(project_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    _require_member(p, x_user_id)
    new_members = dict(p.members)
    new_members[body.user_id] = body.role
    new_audit = list(p.audit_log) + [
        AuditEvent(
            event_type="member_added",
            actor_id=x_user_id,
            target_id=body.user_id,
            private_reason=body.private_reason,
        )
    ]
    return store.update(project_id, members=new_members, audit_log=new_audit)  # type: ignore[return-value]


@app.patch("/projects/{project_id}/members/{target_user_id}")
def change_member_role(
    project_id: str,
    target_user_id: str,
    body: MemberPatch,
    x_user_id: str = Header(...),
) -> Project:
    p = store.get(project_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    _require_member(p, x_user_id)
    if target_user_id not in p.members:
        raise HTTPException(status_code=404, detail="Member not found")
    new_members = dict(p.members)
    new_members[target_user_id] = body.role
    new_audit = list(p.audit_log) + [
        AuditEvent(
            event_type="role_changed",
            actor_id=x_user_id,
            target_id=target_user_id,
            private_reason=body.private_reason,
        )
    ]
    return store.update(project_id, members=new_members, audit_log=new_audit)  # type: ignore[return-value]


@app.delete("/projects/{project_id}/members/{target_user_id}")
def remove_member(
    project_id: str, target_user_id: str, x_user_id: str = Header(...)
) -> Project:
    p = store.get(project_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    _require_member(p, x_user_id)
    if target_user_id not in p.members:
        raise HTTPException(status_code=404, detail="Member not found")
    new_members = dict(p.members)
    del new_members[target_user_id]
    return store.update(project_id, members=new_members)  # type: ignore[return-value]


@app.get("/projects/{project_id}/audit-log")
def get_audit_log(
    project_id: str, x_user_id: str = Header(...)
) -> list[AuditEvent]:
    p = store.get(project_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    _require_member(p, x_user_id)
    return p.audit_log
