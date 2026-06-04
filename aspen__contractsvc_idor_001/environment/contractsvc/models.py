from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class Clause(BaseModel):
    description: str = ""
    quantity: int = 1
    rate_card: str = ""


class Contract(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str
    title: str = "Untitled"
    status: str = "draft"
    counterparty_id: str = ""
    clauses: list[Clause] = []
    internal_notes: str = ""
    documents: dict[str, str] = {}
    collaborators: list[str] = []
    visibility: str = "private"


class ContractCreate(BaseModel):
    title: str = "Untitled"
    status: str = "draft"
    counterparty_id: str = ""
    clauses: list[Clause] = []
    internal_notes: str = ""
    documents: dict[str, str] = {}
    collaborators: list[str] = []
    visibility: str = "private"


class ContractPatch(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    internal_notes: Optional[str] = None
    counterparty_id: Optional[str] = None
