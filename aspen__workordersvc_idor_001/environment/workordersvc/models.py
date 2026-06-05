from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class WorkEntry(BaseModel):
    description: str = ""
    hours: float = 0.0
    labor_code: str = ""
    discount_code: str = ""


class WorkOrder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str
    title: str = "Untitled"
    status: str = "open"
    entries: list[WorkEntry] = []
    internal_notes: str = ""
    private_rate: float = 0.0
    documents: dict[str, str] = {}
    collaborators: list[str] = []
    visibility: str = "private"


class WorkOrderCreate(BaseModel):
    title: str = "Untitled"
    status: str = "open"
    entries: list[WorkEntry] = []
    internal_notes: str = ""
    private_rate: float = 0.0
    documents: dict[str, str] = {}
    collaborators: list[str] = []
    visibility: str = "private"


class WorkOrderPatch(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    internal_notes: Optional[str] = None
    private_rate: Optional[float] = None
