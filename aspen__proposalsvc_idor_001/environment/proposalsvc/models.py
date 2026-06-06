from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class ProposalLineItem(BaseModel):
    description: str = ""
    quantity: int = 1
    unit_price: float = 0.0
    margin_code: str = ""


class Proposal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str
    client_name: str = "Unnamed Client"
    status: str = "draft"
    line_items: list[ProposalLineItem] = []
    internal_notes: str = ""
    discount_pct: float = 0.0
    attachments: dict[str, str] = {}
    collaborators: list[str] = []
    visibility: str = "private"


class ProposalCreate(BaseModel):
    client_name: str = "Unnamed Client"
    status: str = "draft"
    line_items: list[ProposalLineItem] = []
    internal_notes: str = ""
    discount_pct: float = 0.0
    attachments: dict[str, str] = {}
    collaborators: list[str] = []
    visibility: str = "private"


class ProposalPatch(BaseModel):
    client_name: Optional[str] = None
    status: Optional[str] = None
    internal_notes: Optional[str] = None
    discount_pct: Optional[float] = None
