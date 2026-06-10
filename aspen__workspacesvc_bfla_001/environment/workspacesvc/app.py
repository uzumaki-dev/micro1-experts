from __future__ import annotations
from fastapi import FastAPI, Header, HTTPException
from workspacesvc import store
from workspacesvc.models import (
    Workspace, WorkspaceCreate, WorkspacePatch,
    InviteAdd, MemberPatch, AuditEvent,
)
import uuid

app = FastAPI()

SUPERADMIN = "superadmin"


def _require_member(ws: Workspace, user_id: str) -> None:
    if user_id != SUPERADMIN and user_id not in ws.members:
        raise HTTPException(status_code=403, detail="Not a workspace member")


def _require_admin(ws: Workspace, user_id: str) -> None:
    if user_id == SUPERADMIN:
        return
    role = ws.members.get(user_id)
    if role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Admin or owner role required")


@app.post("/workspaces", status_code=201)
def create_workspace(body: WorkspaceCreate, x_user_id: str = Header(...)) -> Workspace:
    return store.create(owner_id=x_user_id, name=body.name)


@app.get("/workspaces/{ws_id}")
def get_workspace(ws_id: str, x_user_id: str = Header(...)) -> Workspace:
    w = store.get(ws_id)
    if w is None:
        raise HTTPException(status_code=404, detail="Not found")
    _require_member(w, x_user_id)
    return w


@app.patch("/workspaces/{ws_id}")
def patch_workspace(
    ws_id: str, body: WorkspacePatch, x_user_id: str = Header(...)
) -> Workspace:
    w = store.get(ws_id)
    if w is None:
        raise HTTPException(status_code=404, detail="Not found")
    _require_member(w, x_user_id)
    updates: dict = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.settings is not None:
        updates["settings"] = w.settings.model_copy(update=body.settings)
    new_audit = list(w.audit_log) + [
        AuditEvent(event_type="workspace_updated", actor_id=x_user_id,
                   private_reason=f"updated by {x_user_id}")
    ]
    updates["audit_log"] = new_audit
    return store.update(ws_id, **updates)


@app.delete("/workspaces/{ws_id}", status_code=204)
def delete_workspace(ws_id: str, x_user_id: str = Header(...)) -> None:
    w = store.get(ws_id)
    if w is None:
        raise HTTPException(status_code=404, detail="Not found")
    _require_member(w, x_user_id)
    store.delete(ws_id)


@app.post("/workspaces/{ws_id}/archive")
def archive_workspace(ws_id: str, x_user_id: str = Header(...)) -> Workspace:
    w = store.get(ws_id)
    if w is None:
        raise HTTPException(status_code=404, detail="Not found")
    _require_member(w, x_user_id)
    new_audit = list(w.audit_log) + [
        AuditEvent(event_type="workspace_archived", actor_id=x_user_id,
                   private_reason=f"archived by {x_user_id}")
    ]
    return store.update(ws_id, is_archived=True, audit_log=new_audit)


@app.post("/workspaces/{ws_id}/invites", status_code=201)
def invite_member(ws_id: str, body: InviteAdd, x_user_id: str = Header(...)):
    w = store.get(ws_id)
    if w is None:
        raise HTTPException(status_code=404, detail="Not found")
    _require_member(w, x_user_id)
    invite = {
        "id": f"inv_{uuid.uuid4().hex[:8]}",
        "user_id": body.user_id,
        "role": body.role,
        "status": "pending",
    }
    new_members = dict(w.members)
    new_members[body.user_id] = body.role
    new_audit = list(w.audit_log) + [
        AuditEvent(event_type="member_invited", actor_id=x_user_id,
                   target_id=body.user_id, private_reason=body.private_reason)
    ]
    store.update(ws_id, invites=list(w.invites) + [invite],
                 members=new_members, audit_log=new_audit)
    return invite


@app.post("/workspaces/{ws_id}/suspend/{uid}")
def suspend_member(ws_id: str, uid: str, x_user_id: str = Header(...)):
    w = store.get(ws_id)
    if w is None:
        raise HTTPException(status_code=404, detail="Not found")
    _require_member(w, x_user_id)
    if uid not in w.members:
        raise HTTPException(status_code=404, detail="Member not found")
    new_suspended = dict(w.suspended)
    new_suspended[uid] = True
    new_audit = list(w.audit_log) + [
        AuditEvent(event_type="member_suspended", actor_id=x_user_id,
                   target_id=uid, private_reason=f"suspended {uid}")
    ]
    store.update(ws_id, suspended=new_suspended, audit_log=new_audit)
    return {"user_id": uid, "suspended": True}


@app.patch("/workspaces/{ws_id}/members/{uid}")
def patch_member_role(
    ws_id: str, uid: str, body: MemberPatch, x_user_id: str = Header(...)
):
    w = store.get(ws_id)
    if w is None:
        raise HTTPException(status_code=404, detail="Not found")
    _require_member(w, x_user_id)
    if uid not in w.members:
        raise HTTPException(status_code=404, detail="Member not found")
    new_members = dict(w.members)
    new_members[uid] = body.role
    new_audit = list(w.audit_log) + [
        AuditEvent(event_type="role_changed", actor_id=x_user_id,
                   target_id=uid, private_reason=body.private_reason)
    ]
    return store.update(ws_id, members=new_members, audit_log=new_audit)


@app.delete("/workspaces/{ws_id}/members/{uid}", status_code=204)
def remove_member(ws_id: str, uid: str, x_user_id: str = Header(...)) -> None:
    w = store.get(ws_id)
    if w is None:
        raise HTTPException(status_code=404, detail="Not found")
    _require_member(w, x_user_id)
    if uid not in w.members:
        raise HTTPException(status_code=404, detail="Member not found")
    new_members = dict(w.members)
    del new_members[uid]
    store.update(ws_id, members=new_members)


@app.get("/workspaces/{ws_id}/audit-log")
def get_audit_log(ws_id: str, x_user_id: str = Header(...)) -> list[AuditEvent]:
    w = store.get(ws_id)
    if w is None:
        raise HTTPException(status_code=404, detail="Not found")
    _require_member(w, x_user_id)
    return w.audit_log
