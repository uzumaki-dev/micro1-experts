from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional
import uuid


class AuditEvent(BaseModel):
    event_type: str
    actor_id: str
    target_id: Optional[str] = None
    private_reason: str = ""
    timestamp: str = "2025-01-01T00:00:00Z"


class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    description: str = ""
    is_archived: bool = False
    owner_id: str
    members: dict[str, str] = Field(default_factory=dict)
    audit_log: list[AuditEvent] = Field(default_factory=list)


class ProjectCreate(BaseModel):
    name: str
    description: str = ""


class ProjectPatch(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class MemberAdd(BaseModel):
    user_id: str
    role: str = "viewer"
    private_reason: str = ""


class MemberPatch(BaseModel):
    role: str
    private_reason: str = ""
