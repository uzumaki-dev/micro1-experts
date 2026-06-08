from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class ClauseEntry(BaseModel):
    clause_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    clause_code: str = ""


class Lease(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str
    tenant_name: str = "Unnamed Tenant"
    property_address: str = ""
    status: str = "draft"
    visibility: str = "private"
    collaborators: list[str] = []
    private_notes: str = ""
    clauses: list[ClauseEntry] = []
    attachments: dict[str, str] = {}


class LeaseCreate(BaseModel):
    tenant_name: str = "Unnamed Tenant"
    property_address: str = ""
    status: str = "draft"
    visibility: str = "private"
    collaborators: list[str] = []
    private_notes: str = ""
    clauses: list[ClauseEntry] = []
    attachments: dict[str, str] = {}


class LeasePatch(BaseModel):
    tenant_name: Optional[str] = None
    property_address: Optional[str] = None
    visibility: Optional[str] = None
    private_notes: Optional[str] = None
