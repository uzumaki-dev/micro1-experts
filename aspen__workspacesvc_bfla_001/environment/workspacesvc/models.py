from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional
import uuid


class WorkspaceSettings(BaseModel):
    sso_enabled: bool = False
    billing_email: str = ""


class AuditEvent(BaseModel):
    event_type: str
    actor_id: str
    target_id: Optional[str] = None
    private_reason: str = ""
    timestamp: str = "2025-01-01T00:00:00Z"


class Workspace(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    is_archived: bool = False
    owner_id: str
    members: dict[str, str] = Field(default_factory=dict)
    suspended: dict[str, bool] = Field(default_factory=dict)
    settings: WorkspaceSettings = Field(default_factory=WorkspaceSettings)
    invites: list[dict] = Field(default_factory=list)
    audit_log: list[AuditEvent] = Field(default_factory=list)


class WorkspaceCreate(BaseModel):
    name: str


class WorkspacePatch(BaseModel):
    name: Optional[str] = None
    settings: Optional[dict] = None


class InviteAdd(BaseModel):
    user_id: str
    role: str = "member"
    private_reason: str = ""


class MemberPatch(BaseModel):
    role: str
    private_reason: str = ""
